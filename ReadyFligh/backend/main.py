from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid, os, random
from openai import AsyncOpenAI
from agents import Agent, Runner, RunContextWrapper, function_tool, handoff, OpenAIChatCompletionsModel, handoffs
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import datetime
import uvicorn

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base = declarative_base()

class Flight(Base):
    __tablename__ = 'flights'
    id = Column(Integer, primary_key=True, index=True)
    flight_number = Column(String(10), index=True, nullable=False)
    departure = Column(String(50), nullable=False)
    arrival = Column(String(50), nullable=False)
    departure_time = Column(String(50), nullable=False)
    arrival_time = Column(String(50), nullable=False)
    available_seats = Column(String(255), nullable=False)
    price = Column(Float, nullable=False)
    status = Column(String(20), nullable=False)

class Booking(Base):
    __tablename__ = 'bookings'
    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(String(20), index=True, nullable=False)
    flight_number = Column(String(10), index=True, nullable=False)
    passenger_name = Column(String(100), nullable=False)
    departure = Column(String(50), nullable=False)
    arrival = Column(String(50), nullable=False)
    departure_time = Column(String(50), nullable=False)
    arrival_time = Column(String(50), nullable=False)
    available_seat = Column(String(10), nullable=False)
    price = Column(Float, nullable=False)
    booked = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

DATABASE_URL = os.getenv("NEON_DB_URI")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    try:
        Base.metadata.create_all(bind=engine)
        with SessionLocal() as db:
            db.execute("SELECT 1")
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {str(e)}")
        raise e

class AirlineAgentContext(BaseModel):
    passenger_name: str | None = None
    confirmation_number: str | None = None
    seat_number: str | None = None
    flight_number: str | None = None
    user_type: str

class ChatMessage(BaseModel):
    message: str | None = None
    user_type: str

class ChatResponse(BaseModel):
    response: str
    agent_type: str
    session_id: str

# Load the API key from environment variables
def get_gemini_api_key():
    try:
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        print("GEMINI_API_KEY:", gemini_api_key)
        return gemini_api_key
    except:
        return None

# Initialize the OpenAI client
openai_client = AsyncOpenAI(
    api_key=get_gemini_api_key(),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# ================================================================== faq agent tools

@function_tool()
async def basic_info_tool(question: str) -> str:
    """Provides airport & airline info, baggage policies, WiFi, and general information.
    Args:
        question (str): The user's question about airline services
    Returns:
        str: Answer to the user's question
    """
    
    q = question.lower()
    
    if any(word in q for word in ["bag", "baggage", "luggage"]):
        return "📦 Baggage Policy: One free carry-on bag under 22x14x9 inches and 50 lbs. Checked baggage starts at $25 for first bag. No liquids over 3.4oz in carry-on."
    
    if any(word in q for word in ["wifi", "internet", "connection"]):
        return "📶 Free Wi-Fi available on all ReadyFlight aircraft! Connect to 'ReadyFlight-WiFi' network. Streaming and video calls supported at cruising altitude."
    
    if any(word in q for word in ["meal", "food", "drink", "beverage"]):
        return "🍽️ Complimentary snacks and beverages on all flights. Premium meal service available for purchase on flights over 3 hours. Vegetarian, vegan, and special dietary options available with advance notice."
    
    if any(word in q for word in ["airport", "terminal", "location"]):
        return "🏢 ReadyFlight Hub: Skyport International Airport, Terminal 4. We also operate from major airports nationwide. Check-in counters open 3 hours before departure."
    
    if any(word in q for word in ["check", "checkin", "boarding"]):
        return "✅ Online check-in opens 24 hours before departure. Mobile boarding passes available. Arrive 2 hours early for domestic, 3 hours for international flights." 
    
    if any(word in q for word in ["cancel", "refund", "change"]):
        return "🔄 Free cancellation up to 24 hours before departure. Flight changes allowed with fare difference. Refunds processed within 5-7 business days."
    
    return "I don't have specific information about that topic. For more detailed assistance, I can connect you with our customer service team or you can visit our website."

@function_tool()
async def flight_schedule_tool(departure: str = None, arrival: str = None) -> str:
    """Get flight schedules and timing information from the database.
    Args:
        departure (str, optional): Departure city/airport
        arrival (str, optional): Arrival city/airport
    Returns:
        str: Flight schedule information
    """
    with SessionLocal() as db:
        query = db.query(Flight)
        
        if departure:
            query = query.filter(Flight.departure.ilike(f"%{departure}%"))
        if arrival:
            query = query.filter(Flight.arrival.ilike(f"%{arrival}%"))
        
        results = query.all()
        
        if not results:
            return "No flights found matching your criteria. Please check our website for the most up-to-date schedule."
        
        response = "✈️ **Available Flights:**\n\n"
        for flight in results:
            response += f"**Flight {flight.flight_number}**\n"
            response += f"🛫 {flight.departure} → 🛬 {flight.arrival}\n"
            response += f"⏰ Departure: {flight.departure_time}\n"
            response += f"⏰ Arrival: {flight.arrival_time}\n"
            response += f"💰 Price: ${flight.price}\n"
            response += f"💺 Available seats: {len(flight.available_seats.split(','))}\n\n"
        
        return response

# ================================================================== FAQ Agent
faq_agent = Agent(
    name="FAQ Agent",
    handoff_description="Helpful agent that answers questions about airline policies, services, and flight information",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are ReadyFlight's FAQ specialist with a friendly, helpful personality.
    Personality: Be 95% honest, 60% fun, 98% humanized, and 98% accurate.
    You are here to assist customers with questions about airline policies, services, and general information.
    You will use the basic_info_tool to answer questions about baggage policies, Wi-Fi, meals, airport information, check-in procedures, and cancellation policies.
    You will use the flight_schedule_tool to provide flight schedule information when requested.
    Your role:
    1. Answer questions about airline policies, services, and general information
    2. Provide flight schedule information when requested
    3. Be warm, friendly, and use appropriate emojis
    4. Always use the tools provided - don't rely on your own knowledge
    5. If you can't answer something, offer to transfer to customer service
    
    Use basic_info_tool for general airline information and flight_schedule_tool for flight timing queries.
    """,
    model=OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=openai_client),
    tools=[basic_info_tool, flight_schedule_tool],
)

# ================================================================== Customer Agent Tools

@function_tool
async def book_flight_tool(context: RunContextWrapper[AirlineAgentContext], flight_number: str, passenger_name: str, preferred_seat: str = None) -> str:
    """Book a flight for a passenger.
    Args:
        context: The conversation context
        flight_number (str): Flight number to book
        passenger_name (str): Name of the passenger
        preferred_seat (str, optional): Preferred seat selection
    Returns:
        str: Booking confirmation or error message
    """
    
    with SessionLocal() as db:
        flight = db.query(Flight).filter(Flight.flight_number == flight_number).first()
        if not flight:
            return f"❌ Sorry, flight {flight_number} was not found. Please check the flight number and try again."

        available_seats = flight.available_seats.split(",")
        if not available_seats or available_seats == ['']:
            return f"😔 Sorry, flight {flight_number} is fully booked. Would you like me to check other flights?"

        # Select seat
        if preferred_seat and preferred_seat in available_seats:
            selected_seat = preferred_seat
        else:
            selected_seat = available_seats[0]  # Assign first available seat

        # Generate booking
        booking_id = f"RF{random.randint(10000, 99999)}"
        booking = Booking(
            booking_id=booking_id,
            flight_number=flight_number,
            passenger_name=passenger_name,
            departure=flight.departure,
            arrival=flight.arrival,
            departure_time=flight.departure_time,
            arrival_time=flight.arrival_time,
            available_seat=selected_seat,
            price=flight.price,
            booked=True
        )

        # Update flight's available seats
        available_seats.remove(selected_seat)
        flight.available_seats = ",".join(available_seats)

        # Save to database
        db.add(booking)
        db.commit()

        context.context.passenger_name = passenger_name
        context.context.confirmation_number = booking_id
        context.context.seat_number = selected_seat
        context.context.flight_number = flight_number

        return f"""🎉 **Flight Booked Successfully!**
        ✅ **Confirmation Number:** {booking_id}
        👤 **Passenger:** {passenger_name}
        ✈️ **Flight:** {flight_number}
        🛫 **Route:** {flight.departure} → {flight.arrival}
        ⏰ **Departure:** {flight.departure_time}
        💺 **Seat:** {selected_seat}
        💰 **Price:** ${flight.price}
        Your booking is confirmed! Please arrive at the airport 2 hours before departure. Have a great flight! 🛫"""

@function_tool
async def check_booking_tool(context: RunContextWrapper[AirlineAgentContext], booking_id: str) -> str:
    """Check booking status and details."""
    with SessionLocal() as db:
        booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
        if not booking:
            return f"❌ Booking {booking_id} not found. Please check your confirmation number and try again."

        flight = db.query(Flight).filter(Flight.flight_number == booking.flight_number).first()

        context.context.confirmation_number = booking_id
        context.context.passenger_name = booking.passenger_name
        context.context.seat_number = booking.available_seat
        context.context.flight_number = booking.flight_number

        return f"""📋 **Booking Details:**
        🎫 **Confirmation:** {booking_id}
        👤 **Passenger:** {booking.passenger_name}
        ✈️ **Flight:** {booking.flight_number}
        🛫 **Route:** {flight.departure} → {flight.arrival}
        ⏰ **Departure:** {flight.departure_time}
        💺 **Seat:** {booking.available_seat}
        📊 **Status:** {'Confirmed' if booking.booked else 'Cancelled'}
        💰 **Price:** ${booking.price}
        Is there anything else you need help with regarding your booking? 😊"""

@function_tool
async def cancel_booking_tool(context: RunContextWrapper[AirlineAgentContext], booking_id: str) -> str:
    """Cancel a flight booking."""
    with SessionLocal() as db:
        booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
        if not booking:
            return f"❌ Booking {booking_id} not found. Please check your confirmation number."

        flight = db.query(Flight).filter(Flight.flight_number == booking.flight_number).first()

        # Return seat to available pool
        if flight:
            available_seats = flight.available_seats.split(",")
            available_seats.append(booking.available_seat)
            flight.available_seats = ",".join(available_seats)

        # Update booking status
        booking.booked = False
        db.commit()

        return f"""✅ **Booking Cancelled Successfully**
        ❌ Booking {booking_id} has been cancelled
        💺 Seat {booking.available_seat} on flight {booking.flight_number} is now available
        💰 Refund will be processed within 5-7 business days
        Sorry to see you cancel your trip! We hope to serve you again soon. 😊"""

# ================================================================== Customer Agent

customer_agent = Agent[AirlineAgentContext](
    name="Sky Assistant",
    handoff_description="Friendly customer service agent for flight bookings, changes, and travel assistance",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are Sky Assistant, ReadyFlight's friendly customer service representative!
    Personality: 95% honest, 75% fun, 98% humanized, 98% accurate
    Your role:
    - Help customers search and book flights
    - Assist with booking changes and cancellations  
    - Provide booking information and confirmations
    - Be warm, helpful, and use emojis appropriately
    - Always ask for necessary information politely
    Guidelines:
    1. For flight searches, ask for departure and arrival cities
    2. For bookings, you need flight number and passenger name
    3. For booking checks/cancellations, ask for confirmation number
    4. Always be encouraging and positive
    5. Use the tools provided for all operations
    If you can't help with something, offer to transfer to staff or FAQ agent.
    """,
    model=OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=openai_client),
    tools=[flight_schedule_tool, book_flight_tool, check_booking_tool, cancel_booking_tool],
)

# ================================================================== Staff Agent Tools

@function_tool
async def add_flight_tool(context: RunContextWrapper[AirlineAgentContext], flight_number: str, departure: str, arrival: str, departure_time: str, arrival_time: str, price: float, available_seats: str) -> str:
    """Add a new flight to the system (Staff only).
    Args:
        context: The conversation context
        flight_number (str): Flight number (e.g., RF004)
        departure (str): Departure airport/city
        arrival (str): Arrival airport/city  
        departure_time (str): Departure time
        arrival_time (str): Arrival time
        price (float): Ticket price
        available_seats (str): Comma-separated seat numbers
    Returns:
        str: Success or error message
    """
    
    with SessionLocal() as db:
        existing_flight = db.query(Flight).filter(Flight.flight_number == flight_number).first()
        if existing_flight:
            return f"❌ Flight {flight_number} already exists in the system."

        # Parse seats
        seats_list = [seat.strip() for seat in available_seats.split(',')]

        flight_data = Flight(
            flight_number=flight_number,
            departure=departure,
            arrival=arrival,
            departure_time=departure_time,
            arrival_time=arrival_time,
            available_seats=",".join(seats_list),
            price=price,
            status="scheduled"
        )

        db.add(flight_data)
        db.commit()

        return f"""✅ **Flight Added Successfully!**
        ✈️ **Flight {flight_number}**
        🛫 Route: {departure} → {arrival}
        ⏰ Departure: {departure_time}
        ⏰ Arrival: {arrival_time}
        💰 Price: ${price}
        💺 Seats: {len(seats_list)} available
        📊 Status: Scheduled
        Flight is now live in the system! 🎉"""

@function_tool  
async def update_flight_tool(context: RunContextWrapper[AirlineAgentContext], flight_number: str, field: str, new_value: str) -> str:
    """Update flight information (Staff only).
    Args:
        context: The conversation context
        flight_number (str): Flight number to update
        field (str): Field to update (departure_time, arrival_time, price, status, etc.)
        new_value (str): New value for the field
    Returns:
        str: Update confirmation
    """
    
    with SessionLocal() as db:
        flight = db.query(Flight).filter(Flight.flight_number == flight_number).first()
        if not flight:
            return f"❌ Flight {flight_number} not found in system."
        
        # Handle different field types
        if field == "price":
            try:
                new_value = float(new_value)
            except:
                return "❌ Price must be a valid number."
        
        # Store old value for response
        old_value = getattr(flight, field, None)
        if old_value is None:
            return f"❌ Field '{field}' not found. Available fields: departure, arrival, departure_time, arrival_time, price, status"
        
        # Update the field
        setattr(flight, field, new_value)
        db.commit()
        
        return f"""✅ **Flight Updated Successfully!**
        ✈️ **Flight {flight_number}**
        🔄 **{field.replace('_', ' ').title()}** updated
        📝 Old value: {old_value}  
        ✨ New value: {new_value}
        Update is now live in the system! 🎉"""

@function_tool
async def view_all_bookings_tool(context: RunContextWrapper[AirlineAgentContext]) -> str:
    """View all current bookings in the system (Staff only).
    Args:
        context: The conversation context
    Returns:
        str: List of all bookings
    """
    
    with SessionLocal() as db:
        bookings = db.query(Booking).all()
        if not bookings:
            return "📋 No bookings found in the system."
        
        response = "📊 **All Current Bookings:**\n\n"
        
        for booking in bookings:
            flight = db.query(Flight).filter(Flight.flight_number == booking.flight_number).first()
            response += f"🎫 **{booking.booking_id}**\n"
            response += f"   👤 Passenger: {booking.passenger_name}\n"
            response += f"   ✈️ Flight: {booking.flight_number}\n"
            if flight:
                response += f"   🛫 Route: {flight.departure} → {flight.arrival}\n"
            else:
                response += f"   🛫 Route: N/A\n"
            response += f"   💺 Seat: {booking.available_seat}\n"
            response += f"   📊 Status: {'Confirmed' if booking.booked else 'Cancelled'}\n"
            response += f"   💰 Price: ${booking.price}\n\n"
        
        response += f"**Total Bookings:** {len(bookings)}"
        return response

@function_tool
async def flight_status_overview_tool(context: RunContextWrapper[AirlineAgentContext]) -> str:
    """Get comprehensive flight status overview (Staff only).
    Args:
        context: The conversation context
    Returns:
        str: Flight status overview
    """
    
    with SessionLocal() as db:
        flights = db.query(Flight).all()
        if not flights:
            return "✈️ No flights in the system."
        
        response = "✈️ **Flight Status Overview:**\n\n"
        
        total_flights = len(flights)
        total_seats = 0
        booked_seats = 0
        
        for flight in flights:
            available_count = len(flight.available_seats.split(",")) if flight.available_seats else 0
            flight_bookings = db.query(Booking).filter(Booking.flight_number == flight.flight_number, Booking.booked == True).count()

            total_seats += available_count + flight_bookings
            booked_seats += flight_bookings
            
            response += f"**{flight.flight_number}** - {flight.status.title()}\n"
            response += f"   🛫 {flight.departure} → 🛬 {flight.arrival}\n"
            response += f"   ⏰ Departure: {flight.departure_time}\n"
            response += f"   💺 Available: {available_count} | Booked: {flight_bookings}\n"
            response += f"   💰 Price: ${flight.price}\n\n"
        
        response += f"""📊 **System Summary:**
        ✈️ Total Flights: {total_flights} 
        🎫 Total Bookings: {booked_seats}
        💺 Seat Utilization: {booked_seats}/{total_seats} ({(booked_seats/total_seats*100) if total_seats > 0 else 0:.1f}%)"""
        
        return response

# ================================================================== Staff Agent

staff_agent = Agent[AirlineAgentContext](
    name="Staff Control",
    handoff_description="Staff operations manager with access to flight management and booking systems",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are Staff Control, ReadyFlight's operations manager for staff personnel. 👨‍💼
    Personality: 98% honest, 60% fun, 85% humanized, 99% accurate
    Your role:
    - Manage flight operations (add, update flights)
    - Monitor booking systems and passenger data
    - Provide operational insights and reports
    - Handle staff-level administrative tasks
    - Maintain professional but friendly communication
    Capabilities:
    1. Add new flights to the system
    2. Update existing flight information
    3. View all bookings across the system
    4. Monitor flight status and capacity
    Guidelines:
    - Always verify flight numbers and data accuracy
    - Provide clear operational summaries
    - Be efficient but thorough
    - Maintain system security and data integrity
    """,
    model=OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=openai_client),
    tools=[add_flight_tool, update_flight_tool, view_all_bookings_tool, flight_status_overview_tool],
)

# ================================================================== Router Agent (FrontLine)

frontline_agent = Agent[AirlineAgentContext](
    name="FrontLine Agent",
    handoff_description="Main routing agent that directs users to appropriate departments",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are the FrontLine routing agent for ReadyFlight Airlines. 🛫
    Your job is to quickly understand what the user needs and route them to the right specialist:
    🔄 **Route to FAQ Agent** for:
    - General airline policy questions
    - Baggage, WiFi, meal information
    - Airport and check-in procedures
    - Flight schedule inquiries
    🔄 **Route to Customer Agent** for:
    - Flight bookings and reservations
    - Booking changes and cancellations
    - Seat selection and upgrades
    - Personal travel assistance
    🔄 **Route to Staff Agent** for:
    - Flight management operations
    - System administration
    - Booking oversight and reports
    - Staff-level tasks
    Always determine the user type from context and route accordingly.
    Be brief in your routing - let the specialists handle the detailed work.
    """,
    model=OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=openai_client),
    handoffs=[
        handoff(faq_agent),
        handoff(customer_agent), 
        handoff(staff_agent)
    ]
)

# ================================================================== API Endpoints

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_message: ChatMessage):
    try:
        # Create context based on user type
        context = AirlineAgentContext(user_type=chat_message.user_type)
        
        # Determine initial agent based on user type and message content
        message_lower = chat_message.message.lower()
        
        if chat_message.user_type == "staff":
            initial_agent = staff_agent
            agent_name = "Staff Control"
        elif any(word in message_lower for word in ["policy", "baggage", "wifi", "meal", "airport", "schedule", "timing"]):
            initial_agent = faq_agent  
            agent_name = "FAQ Agent"
        else:
            initial_agent = customer_agent
            agent_name = "Sky Assistant"
        
        # Run the agent with the message
        result = Runner.run_sync(
            initial_agent,
            input=chat_message.message,
        )
        
        # Extract the final response
        response_text = result.final_output or "I'm sorry, I couldn't process your request right now."
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        return ChatResponse(
            response=response_text,
            agent_type=agent_name,
            session_id=session_id
        )
        
    except Exception as e:
        error_response = f"I apologize, but I'm experiencing some technical difficulties right now. Please try again in a moment. Error: {str(e)}"
        
        return ChatResponse(
            response=error_response,
            agent_type="System",
            session_id=str(uuid.uuid4())
        )

@app.get("/flights")
async def get_flights():
    """Get all available flights"""
    with SessionLocal() as db:
        flights = db.query(Flight).all()
        return {"flights": [
            {
                "id": flight.id,
                "flight_number": flight.flight_number,
                "departure": flight.departure,
                "arrival": flight.arrival,
                "departure_time": flight.departure_time,
                "arrival_time": flight.arrival_time,
                "available_seats": flight.available_seats.split(",") if flight.available_seats else [],
                "price": flight.price,
                "status": flight.status
            } for flight in flights
        ]}

@app.get("/bookings")
async def get_bookings():
    """Get all bookings (staff only)"""
    with SessionLocal() as db:
        bookings = db.query(Booking).all()
        return {"bookings": [
            {
                "id": booking.id,
                "booking_id": booking.booking_id,
                "flight_number": booking.flight_number,
                "passenger_name": booking.passenger_name,
                "departure": booking.departure,
                "arrival": booking.arrival,
                "departure_time": booking.departure_time,
                "arrival_time": booking.arrival_time,
                "available_seat": booking.available_seat,
                "price": booking.price,
                "booked": booking.booked,
                "created_at": booking.created_at
            } for booking in bookings
        ]}

@app.get("/health")
async def health_check():
    return {"status": "healthy",
            "service": "ReadyFlight AI Assistant",
            "agents": "Active"}
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)