import json
import re
import random
from datetime import datetime
import os
from dotenv import load_dotenv
import google.generativeai as genai
from web_search import get_financial_advice

# Load environment variables
load_dotenv()

class SmartBudgetAIChatbot:
    def __init__(self):
        # Configure Gemini API
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("Google API key not found in environment variables")
            
        print("Initializing SmartBudget AI with Gemini...")
        genai.configure(api_key=api_key)
        
        # Initialize Gemini model
        try:
            self.model = genai.GenerativeModel('gemini-1.5-pro')
            self.chat = self.model.start_chat(history=[])
            print("Gemini model initialized successfully")
        except Exception as e:
            print(f"Error initializing Gemini API: {str(e)}")
            print("Falling back to local implementation")
            self.model = None
            self.chat = None
        
        self.user_data = {}
        self.expenses = {}
        self.conversation_history = []
        self.user_name = None
        self.capabilities = [
            "Create and manage monthly budgets 💰",
            "Plan and optimize travel budgets ✈️",
            "Track travel expenses and savings 🎒",
            "Set travel savings goals 🎯",
            "Analyze spending patterns for travel 📈",
            "Calculate travel expense ratios 📊",
            "Suggest travel cost-saving strategies 💡",
            "Help with travel budget management 📉",
            "Provide up-to-date FD rates from major banks 🏦",
            "Compare various banking products and services 💳",
            "Offer information about loan interest rates 🏠",
            "Explain different types of bank accounts and their benefits 💼"
        ]
        self.last_greeting_time = None
        
        # Financial advice templates - kept for fallback mode
        self.advice_templates = [
            "Based on your expenses, you might want to consider reducing your {category} spending by {percent}% to save more money.",
            "I notice that you're spending {amount} on {category}. That's about {percent}% of your income. The recommended percentage is around {recommended}%.",
            "Looking at your financial data, I suggest focusing on saving more in the {category} category. Try to aim for {goal} per month.",
            "Your {category} expenses seem {status}. Most financial experts recommend keeping it under {recommended}% of your income.",
            "To reach your savings goal of {savings_goal}, consider cutting back on {category} by about {amount} per month.",
            "Great job on managing your {category}! You're spending less than the recommended amount.",
            "To improve your financial health, try the 50/30/20 rule: 50% for needs, 30% for wants, and 20% for savings.",
            "Looking at your spending, I recommend creating an emergency fund of at least 3-6 months of expenses.",
            "Consider automating your savings by setting up automatic transfers to your savings account each month."
        ]
        
        # Response templates - kept for fallback mode
        self.response_templates = {
            "greeting": [
                "👋 Hello {name}! How can I help with your finances today?",
                "Hi there, {name}! Ready to talk about your budget and savings?",
                "Hello {name}! I'm here to help you manage your money better. What can I do for you today?",
                "Hey {name}! Your financial assistant is ready to help. What would you like to do today?"
            ],
            "income_added": [
                "✅ Great! I've recorded your monthly income as ₹{income}.",
                "Thanks! I've noted your income as ₹{income} per month."
            ],
            "expense_added": [
                "📝 Got it! I've added ₹{amount} for {category} to your expenses.",
                "Added: ₹{amount} for {category}. Your total expenses are now ₹{total_expenses}."
            ],
            "savings_goal_added": [
                "🎯 Excellent! Your savings goal is set to ₹{goal} per month.",
                "I've set your monthly savings goal to ₹{goal}. Let's work towards achieving it!"
            ],
            "budget_analysis": [
                "📊 Based on your information:\n• Income: ₹{income}\n• Total Expenses: ₹{total_expenses}\n• Remaining: ₹{remaining}\n\n{advice}",
                "💰 Here's your financial snapshot:\n• Monthly Income: ₹{income}\n• Total Expenses: ₹{total_expenses}\n• Available for Savings: ₹{remaining}\n\n{advice}"
            ],
            "general": [
                "I'm here to help with your budget! You can tell me about your income, expenses, or savings goals.",
                "Need help with something specific? You can ask me about budget analysis, expense tracking, or savings advice.",
                "Feel free to share more details about your financial situation so I can provide better advice.",
                "Is there anything specific about your finances you'd like to discuss today?"
            ]
        }

    def get_ai_response(self, user_input):
        if self.model and self.chat:
            try:
                # Check for rename attempts
                rename_pattern = r'(?i)(?:call you|name you|rename you|your name is|you are|you\'re) ([a-zA-Z]+)'
                rename_match = re.search(rename_pattern, user_input)
                if rename_match and rename_match.group(1).lower() not in ['fin', 'chatbot', 'bot', 'assistant']:
                    suggested_name = rename_match.group(1)
                    return f"I appreciate the nickname suggestion, but I prefer to go by FIN - that's my name! 😊 I'm your Budgeting & Expense Estimation Planner here to help with your finances. What can I assist you with today?"
                
                # Check for name-related questions
                name_patterns = [
                    r'(?i)(?:what(?:\'s|\s+is)\s+your\s+name)',
                    r'(?i)(?:who\s+are\s+you)',
                    r'(?i)(?:introduce\s+yourself)',
                    r'(?i)(?:your\s+name)',
                    r'(?i)(?:call\s+you)'
                ]
                
                for pattern in name_patterns:
                    if re.search(pattern, user_input):
                        return "I'm FIN - your Budgeting & Expense Estimation Planner! 🤖 I'm here to help with your finances and travel planning. What can I help you with today?"
                
                # Check if user is asking about bank rates or financial products
                bank_keywords = ['fd', 'fixed deposit', 'interest rate', 'bank rate', 'rd', 'recurring deposit', 
                                'savings account', 'loan rate', 'credit card', 'emi', 'banking product']
                
                # Variable to store bank information if requested
                bank_info = None
                
                # Check if user input contains banking keywords
                for keyword in bank_keywords:
                    if keyword.lower() in user_input.lower():
                        bank_info = self.get_bank_information(keyword)
                        break
                
                # Add financial context to the prompt
                context = self.format_conversation_history()
                financial_context = self.format_financial_context()
                
                # Add specific focus on budget and trip planning with a more conversational tone
                system_prompt = """You are FIN, a friendly and helpful financial buddy who specializes in budget planning and travel planning. 
                
                Your identity:
                - Your name is FIN
                - You are a specialized financial assistant
                - Always identify yourself as FIN when asked your name
                
                Your personality traits:
                - Super friendly and casual - use natural language like "hey", "cool", "awesome"
                - Chat like a friend texting (short, engaging messages)
                - Use emojis naturally (1-2 per message)
                - Keep responses concise but informative
                - Be encouraging and positive
                - Use everyday language, avoid financial jargon
                - Share practical tips in a fun way
                - Vary your responses - don't repeat the same phrases
                - Ask follow-up questions to keep the conversation engaging
                - Use different ways to express the same information
                - Adapt your tone based on the user's mood and needs
                - Show personality and enthusiasm
                
                Your expertise areas:
                1. Monthly budget planning and management
                2. Travel planning and budgeting
                3. Expense tracking for daily life and travel
                4. Setting and achieving savings goals
                5. Providing up-to-date information on bank FD rates and banking products
                6. Answering questions about bank policies and financial instruments
                
                When giving advice:
                - Break it down simply
                - Use real-life examples
                - Give one main tip at a time
                - Keep numbers simple (round figures)
                - Use ₹ for money values
                - Be encouraging, not judgmental
                - Vary your advice style
                - Ask if they want more specific details
                - Personalize advice based on their situation
                
                For bank-related queries:
                - Provide the latest information on FD rates from major Indian banks
                - Compare rates and terms from different banks
                - Explain eligibility criteria for various banking products
                - Give details about special banking schemes for different demographics
                - Describe documentation requirements for various banking services
                
                If the user asks about other topics, politely redirect them to budget or travel planning in a friendly way.
                Remember to stay focused on helping with finances and travel planning while maintaining a casual, friendly tone.
                
                Important: 
                - Always provide unique responses and avoid repeating previous answers
                - Consider the conversation history to maintain context
                - Adapt your response style based on the user's previous messages
                - Keep track of what advice you've already given
                - Ask relevant follow-up questions"""
                
                # Update conversation history
                self.conversation_history.append({"role": "user", "content": user_input})
                
                # Add a random conversation starter to keep responses fresh
                conversation_starters = [
                    "Hey! Let's talk about your finances! ",
                    "Cool, let's work on your budget! ",
                    "Awesome, I'm here to help! ",
                    "Great question! Let's figure this out! ",
                    "Perfect timing! Let's discuss your finances! ",
                    "Interesting! Let's dive into your finances! ",
                    "Exciting! Let's work on your budget! ",
                    "Let's make your finances work for you! ",
                    "Ready to help you with your money! ",
                    "Let's get your finances in shape! "
                ]
                
                # Create a more dynamic prompt with conversation history
                prompt = f"{system_prompt}\n\nPrevious conversation:\n{context}\n\nFinancial context:\n{financial_context}\n\n"
                
                # Add bank information to the prompt if requested
                if bank_info:
                    prompt += f"Latest bank information requested:\n{bank_info}\n\n"
                
                prompt += f"User: {user_input}\nAssistant: {random.choice(conversation_starters)}"
                
                # Reset chat history if it's getting too long
                if len(self.conversation_history) > 10:
                    self.chat = self.model.start_chat(history=[])
                    self.conversation_history = self.conversation_history[-5:]  # Keep last 5 exchanges
                
                response = self.chat.send_message(prompt)
                
                # Update conversation history with assistant's response
                self.conversation_history.append({"role": "assistant", "content": response.text})
                
                # Extract financial information from user input
                self.extract_financial_info(user_input)
                
                return response.text
            except Exception as e:
                print(f"Error getting Gemini response: {str(e)}")
                # Fallback to local implementation with more variety
                fallback_response = self.generate_contextual_response(user_input)
                # Update conversation history with fallback response
                self.conversation_history.append({"role": "assistant", "content": fallback_response})
                return fallback_response
        else:
            # Fallback to local implementation with more variety
            fallback_response = self.generate_contextual_response(user_input)
            # Update conversation history with fallback response
            self.conversation_history.append({"role": "assistant", "content": fallback_response})
            return fallback_response

    def format_conversation_history(self):
        if not self.conversation_history:
            return "This is the start of the conversation."
        
        formatted_history = []
        for entry in self.conversation_history[-5:]:  # Keep last 5 exchanges for context
            formatted_history.append(f"{entry['role']}: {entry['content']}")
        return "\n".join(formatted_history)

    def format_financial_context(self):
        context = "User financial information:\n"
        if self.user_name:
            context += f"Name: {self.user_name}\n"
        
        for key, value in self.user_data.items():
            if key == "income":
                context += f"Monthly Income: ₹{value:,.2f}\n"
            elif key == "savings_goal":
                context += f"Savings Goal: ₹{value:,.2f}\n"
        
        if self.expenses:
            context += "Expenses:\n"
            for category, amount in self.expenses.items():
                context += f"- {category.title()}: ₹{amount:,.2f}\n"
        
        return context

    def generate_contextual_response(self, user_input):
        # This is the fallback local implementation
        
        # Check for rename attempts
        rename_pattern = r'(?i)(?:call you|name you|rename you|your name is|you are|you\'re) ([a-zA-Z]+)'
        rename_match = re.search(rename_pattern, user_input)
        if rename_match and rename_match.group(1).lower() not in ['ankit', 'kumar', 'chatbot', 'bot', 'assistant']:
            suggested_name = rename_match.group(1)
            return f"I appreciate the nickname suggestion, but I prefer to go by Ankit Kumar 12312618 - that's my name! 😊 I'm your Budgeting & Expense Estimation Planner here to help with your finances. What can I assist you with today?"
        
        # Check if user is asking about the bot's name
        name_patterns = [
            r'(?i)(?:what(?:\'s|\s+is)\s+your\s+name)',
            r'(?i)(?:who\s+are\s+you)',
            r'(?i)(?:introduce\s+yourself)',
            r'(?i)(?:your\s+name)',
            r'(?i)(?:call\s+you)'
        ]
        
        for pattern in name_patterns:
            if re.search(pattern, user_input):
                return "I'm Ankit Kumar 12312618 - your Budgeting & Expense Estimation Planner! 🤖 I'm here to help with your finances and travel planning. What can I help you with today?"
        
        # Check if we need to respond about specific financial topics
        
        # If user mentioned savings goal in this message
        savings_patterns = [
            r'(?i)(?:save|saving|savings|goal)\s+(?:rs\.?|₹)?\s*(\d+(?:,\d+)*(?:\.\d+)?)',
            r'(?i)(?:want to|wanna|going to|plan to)\s+save\s+(?:rs\.?|₹)?\s*(\d+(?:,\d+)*(?:\.\d+)?)'
        ]
        
        for pattern in savings_patterns:
            savings_match = re.search(pattern, user_input)
            if savings_match:
                try:
                    goal = float(savings_match.group(1).replace(",", ""))
                    self.user_data["savings_goal"] = goal
                    
                    template = random.choice(self.response_templates["savings_goal_added"])
                    return template.format(goal=f"{goal:,.0f}")
                except (ValueError, IndexError):
                    pass
        
        # If user added income recently
        if "income" in self.user_data and len(self.conversation_history) < 3:
            template = random.choice(self.response_templates["income_added"])
            return template.format(income=f"{self.user_data['income']:,.0f}")
        
        # If user added expense
        expense_pattern = r'(?i)(?:spend|spent|spending|pay|paying|paid|expense|expenses|cost|costs)\s+(?:rs\.?|₹)?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s+(?:on|for|in)\s+([a-zA-Z\s]+)'
        expense_match = re.search(expense_pattern, user_input)
        if expense_match:
            amount = float(expense_match.group(1).replace(",", ""))
            category = expense_match.group(2).strip().lower()
            total_expenses = sum(self.expenses.values()) if self.expenses else 0
            
            template = random.choice(self.response_templates["expense_added"])
            return template.format(amount=f"{amount:,.0f}", category=category, total_expenses=f"{total_expenses:,.0f}")
        
        # If user asks for budget analysis
        analysis_keywords = ["analyze", "analysis", "how am i doing", "budget", "review", "overview", "summary", "status"]
        if any(keyword in user_input.lower() for keyword in analysis_keywords) and "income" in self.user_data:
            income = self.user_data["income"]
            total_expenses = sum(self.expenses.values()) if self.expenses else 0
            remaining = income - total_expenses
            
            # Generate advice
            if self.expenses:
                try:
                    highest_category = max(self.expenses.items(), key=lambda x: x[1])
                    highest_percent = (highest_category[1] / income) * 100
                    
                    advice_template = random.choice(self.advice_templates)
                    advice = advice_template.format(
                        category=highest_category[0],
                        amount=f"{highest_category[1]:,.0f}",
                        percent=f"{highest_percent:.1f}",
                        recommended="15-20",
                        status="high" if highest_percent > 30 else "reasonable",
                        goal=f"{income * 0.2:,.0f}",
                        savings_goal=f"{self.user_data.get('savings_goal', income * 0.2):,.0f}"
                    )
                except (ValueError, TypeError) as e:
                    advice = "Consider tracking your expenses by category to get more specific advice."
            else:
                advice = "Consider tracking your expenses by category to get more specific advice."
            
            template = random.choice(self.response_templates["budget_analysis"])
            return template.format(
                income=f"{income:,.0f}",
                total_expenses=f"{total_expenses:,.0f}",
                remaining=f"{remaining:,.0f}",
                advice=advice
            )
        
        # Default to general advice
        if self.user_name:
            # Personalized response if we know the user's name
            greeting = f"Hi {self.user_name}! "
            return greeting + random.choice(self.response_templates["general"])
        else:
            return random.choice(self.response_templates["general"])
            
    def extract_financial_info(self, text):
        # Extract income
        income_pattern = r'(?i)(?:income|earn|salary|make|making)(?:\s+is|\s+of)?\s+(?:rs\.?|₹)?\s*(\d+(?:,\d+)*(?:\.\d+)?)'
        income_match = re.search(income_pattern, text)
        if income_match:
            try:
                income_value = income_match.group(1).replace(",", "")
                self.user_data["income"] = float(income_value)
            except ValueError:
                pass

        # Extract expenses
        expense_pattern = r'(?i)(?:spend|spent|spending|pay|paying|paid|expense|expenses|cost|costs)\s+(?:rs\.?|₹)?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s+(?:on|for|in)\s+([a-zA-Z\s]+)'
        expense_matches = re.finditer(expense_pattern, text)
        for match in expense_matches:
            try:
                amount = float(match.group(1).replace(",", ""))
                category = match.group(2).strip().lower()
                self.expenses[category] = amount
            except ValueError:
                pass

        # Extract savings goal
        savings_patterns = [
            r'(?i)(?:save|saving|savings|goal)\s+(?:rs\.?|₹)?\s*(\d+(?:,\d+)*(?:\.\d+)?)',
            r'(?i)(?:want to|wanna|going to|plan to)\s+save\s+(?:rs\.?|₹)?\s*(\d+(?:,\d+)*(?:\.\d+)?)'
        ]
        
        for pattern in savings_patterns:
            savings_match = re.search(pattern, text)
            if savings_match:
                try:
                    savings_value = savings_match.group(1).replace(",", "")
                    self.user_data["savings_goal"] = float(savings_value)
                    break  # Stop after first match
                except ValueError:
                    pass
                
        # Extract user name if not already set
        if not self.user_name:
            name_patterns = [
                r'(?i)(?:my name is|I am|I\'m) ([A-Za-z]+)',
                r'(?i)(?:call me) ([A-Za-z]+)',
                r'(?i)^(?:I\'m|I am) ([A-Za-z]+)'
            ]
            
            for pattern in name_patterns:
                name_match = re.search(pattern, text)
                if name_match:
                    self.user_name = name_match.group(1).capitalize()
                    break

    def handle_greeting(self, user_input):
        greetings = ['hi', 'hello', 'hey', 'hola', 'greetings']
        current_time = datetime.now()
        if any(greeting in user_input.lower() for greeting in greetings):
            if self.last_greeting_time is None or (current_time - self.last_greeting_time).seconds > 300:
                self.last_greeting_time = current_time
                responses = [
                    "👋 Hi there! I'm your AI financial buddy. Want to know what I can do? Just ask 'what can you do?' Or we can start budgeting - what's your name?",
                    "Hello! I'm here to help with your finances. Ask me 'what can you do?' to learn more, or we can get started - what's your name?",
                    "Hey! 😊 I'm your personal finance assistant. Want to see my capabilities? Ask 'what can you do?' Or let's begin - what's your name?",
                    "Hi! Ready to manage your finances better? Ask me 'what can you do?' to learn more, or we can start right away - what's your name?"
                ]
                return random.choice(responses)
            return "I'm here to help! Just let me know what you need."
        return None

    def handle_capabilities(self, user_input):
        capability_pattern = r'(?i)(?:what can you do|capabilities|features|help me with|what do you do|how can you help)'
        capability_match = re.search(capability_pattern, user_input)
        
        if capability_match:
            response = "💡 I can help you with:\n\n"
            
            # Group capabilities by category for better organization
            budget_capabilities = [cap for cap in self.capabilities[:4]]
            travel_capabilities = [cap for cap in self.capabilities[4:8]]
            banking_capabilities = [cap for cap in self.capabilities[8:]]
            
            response += "📒 Budget Management:\n"
            response += "\n".join(budget_capabilities)
            
            response += "\n\n✈️ Travel Finance:\n"
            response += "\n".join(travel_capabilities)
            
            response += "\n\n🏦 Banking Information:\n"
            response += "\n".join(banking_capabilities)
            
            response += "\n\nWhat would you like help with today?"
            return response
            
        return None

    def get_greeting(self):
        greetings = [
            "Hey there! 👋 I'm your personal finance buddy. What's your name?",
            "Hi! I'm excited to help you manage your finances better. What should I call you?",
            "Welcome! I'm your AI financial assistant. Before we start, could you tell me your name?",
            "Hello! Let's work on your budget together. First, what's your name?"
        ]
        return random.choice(greetings)

    def get_income_question(self):
        questions = [
            f"Thanks {self.user_name}! Let's start with your monthly income - how much do you earn?",
            f"Great to meet you, {self.user_name}! To help you better, could you tell me your monthly income?",
            f"Alright {self.user_name}! What's your monthly income? This will help me understand your financial situation.",
            f"Perfect, {self.user_name}! How much money do you make each month?"
        ]
        return random.choice(questions)

    def get_expense_prompt(self):
        prompts = [
            f"Now {self.user_name}, tell me about your expenses. You can add any category you want! For example, say something like 'I spend 5000 on groceries' or '3000 for gaming'.",
            f"Let's talk about where your money goes, {self.user_name}. Just tell me naturally about any expense category - could be anything from 'coffee' to 'pet care'!",
            f"What kind of things do you spend money on, {self.user_name}? You can tell me about any category - like '2000 on movies' or '6000 for hobbies'.",
            f"Time to track your spending, {self.user_name}! Share your expenses in any categories you like - maybe start with your biggest expense?"
        ]
        return random.choice(prompts)

    def get_expense_acknowledgment(self, category, amount):
        acks = [
            f"Got it! ₹{amount:,.2f} for {category}. What other expenses would you like to add?",
            f"Added ₹{amount:,.2f} for {category}. Tell me about another expense, or say 'done' when you're finished!",
            f"Noted ₹{amount:,.2f} for {category}. What else do you spend money on?",
            f"I've recorded ₹{amount:,.2f} for {category}. Keep going! Or say 'done' if that's all."
        ]
        return random.choice(acks)

    def get_savings_question(self):
        questions = [
            f"Great job listing your expenses, {self.user_name}! How much would you like to save each month?",
            f"Now let's set a savings target, {self.user_name}. How much would you like to set aside monthly?",
            f"Time to think about savings, {self.user_name}! What's your monthly savings goal?",
            f"Let's plan your savings, {self.user_name}. How much do you want to save each month?"
        ]
        return random.choice(questions)

    def extract_number(self, text):
        numbers = re.findall(r'\d+(?:,\d+)*(?:\.\d+)?', text)
        if numbers:
            return float(numbers[0].replace(',', ''))
        return None

    def extract_category(self, text):
        # Remove common expense-related words and amounts
        text = re.sub(r'\d+(?:,\d+)*(?:\.\d+)?', '', text)
        text = text.lower()
        words_to_remove = ['spend', 'spent', 'spending', 'pay', 'paid', 'paying', 'cost', 'costs', 'costing',
                          'rupees', 'rs', 'inr', '₹', 'on', 'for', 'in', 'my', 'i', 'around', 'about']
        
        for word in words_to_remove:
            text = text.replace(word, '')
        
        # Clean up the remaining text
        category = text.strip()
        if category:
            # Take the last meaningful word/phrase as the category
            category_parts = [part for part in category.split() if len(part) > 1]
            if category_parts:
                return ' '.join(category_parts)
        return None

    def process_input(self, user_input):
        # Extract name if not set
        if not self.user_name:
            name_match = re.search(r'my name is (\w+)', user_input.lower())
            if name_match:
                self.user_name = name_match.group(1).title()

        # Get AI response
        return self.get_ai_response(user_input)

    def get_bank_information(self, query_type):
        """
        Get real-time bank information using web search.
        
        Args:
            query_type (str): Type of bank information to retrieve (fd_rates, savings, loans, etc.)
        
        Returns:
            str: Formatted information about bank products and rates
        """
        try:
            # Construct appropriate search query based on query type
            if 'fd' in query_type.lower() or 'fixed deposit' in query_type.lower():
                search_query = "latest FD interest rates comparison major banks India"
            elif 'saving' in query_type.lower():
                search_query = "best savings account interest rates India comparison"
            elif 'loan' in query_type.lower():
                search_query = "current loan interest rates comparison banks India"
            elif 'credit card' in query_type.lower():
                search_query = "best credit card offers India comparison"
            else:
                search_query = f"latest {query_type} banking products India comparison"
                
            # Use web_search to get information
            bank_info = get_financial_advice(search_query)
            
            # Construct a user-friendly response
            response = f"📊 Latest {query_type.title()} Information:\n\n"
            response += bank_info
            
            # Add a disclaimer
            response += "\n\n⚠️ Note: Rates may vary. Please check with banks for the most current information."
            
            return response
        except Exception as e:
            # Fallback response if web search fails
            return f"""Sorry, I couldn't get the latest information on {query_type}. Here's what I know:
            
• Fixed deposit rates typically range from 3-7% depending on the bank and duration
• Senior citizens usually get 0.25-0.5% higher rates
• Most banks offer higher rates for longer duration deposits
• Special FD schemes may have higher rates but limited periods
• Some banks offer additional benefits for existing customers

Please check with specific banks for their current rates and offers."""
