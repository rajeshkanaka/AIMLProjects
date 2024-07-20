# Final One-Week U.S. Property Market Chatbot Prototype Plan and Script

## Development Plan

### Day 1: Setup and Core API Integration (8 hours)

1. Set up development environment (1 hour)
2. Implement Zillow API integration with rate limiting (5 hours)
3. Create basic property data retrieval function (2 hours)

### Day 2: Basic Chatbot Enhancement (8 hours)

1. Expand qa_dict with more relevant entries (2 hours)
2. Implement property value query handling (3 hours)
3. Develop simple property comparison feature (3 hours)

### Day 3-4: Form Filling and Integration (16 hours)

1. Design and implement AutoVal order form structure (4 hours)
2. Create conversation flow for form filling (6 hours)
3. Integrate form filling with main chatbot logic (4 hours)
4. Implement input validation and error handling (2 hours)

### Day 5: Testing and Refinement (8 hours)

1. Develop and run test cases for all features (4 hours)
2. Fix bugs and refine conversation flows (4 hours)

### Day 6: User Experience Improvements (8 hours)

1. Implement help command and user guide (2 hours)
2. Create engaging introduction and improve overall tone (2 hours)
3. Add basic feedback mechanism for demo (2 hours)
4. Final testing and refinements (2 hours)

### Day 7: Documentation and Demo Preparation (8 hours)

1. Write brief documentation for the prototype (3 hours)
2. Prepare compelling demo script (3 hours)
3. Team briefing on prototype usage and demo (2 hours)

## Chatbot Script

```python
import os
import time
import requests
from dotenv import load_dotenv
import xml.etree.ElementTree as ET
import re

load_dotenv()
ZILLOW_API_KEY = os.getenv('ZILLOW_API_KEY')

class RateLimiter:
    def __init__(self, calls_per_second):
        self.calls_per_second = calls_per_second
        self.last_call_time = 0

    def wait(self):
        current_time = time.time()
        time_since_last_call = current_time - self.last_call_time
        if time_since_last_call < 1 / self.calls_per_second:
            time.sleep((1 / self.calls_per_second) - time_since_last_call)
        self.last_call_time = time.time()

rate_limiter = RateLimiter(calls_per_second=5)  # Adjust as per Zillow's rate limits

def get_property_details(address, citystatezip):
    """Fetch basic property details from Zillow API with rate limiting and error handling"""
    rate_limiter.wait()

    base_url = "http://www.zillow.com/webservice/GetSearchResults.htm"
    params = {
        'zws-id': ZILLOW_API_KEY,
        'address': address,
        'citystatezip': citystatezip
    }

    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()

        root = ET.fromstring(response.content)

        error_code = root.find('.//code')
        if error_code is not None and error_code.text != '0':
            error_msg = root.find('.//message').text
            raise ValueError(f"Zillow API Error: {error_msg}")

        zpid = root.find('.//zpid')
        zestimate = root.find('.//zestimate/amount')

        if zpid is None or zestimate is None:
            raise ValueError("Required data not found in API response")

        return {
            'zpid': zpid.text,
            'zestimate': zestimate.text
        }
    except requests.RequestException as e:
        print(f"API request failed: {str(e)}")
    except ValueError as e:
        print(str(e))
    except ET.ParseError:
        print("Failed to parse API response")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")

    return None

def integrate_zillow_data(chatbot_response, address, citystatezip):
    """Integrate Zillow data into chatbot response with fallback"""
    property_data = get_property_details(address, citystatezip)
    if property_data:
        return f"{chatbot_response} The estimated value of the property is ${property_data['zestimate']}."
    return f"{chatbot_response} I'm sorry, I couldn't retrieve the property value at this time."

def compare_properties(address1, citystatezip1, address2, citystatezip2):
    """Compare two properties based on their Zestimates"""
    property1 = get_property_details(address1, citystatezip1)
    property2 = get_property_details(address2, citystatezip2)

    if property1 is None or property2 is None:
        return "I'm sorry, I couldn't retrieve the information for one or both properties."

    zestimate1 = int(property1['zestimate'])
    zestimate2 = int(property2['zestimate'])
    difference = abs(zestimate1 - zestimate2)
    percentage = (difference / min(zestimate1, zestimate2)) * 100

    response = f"Here's a comparison of the two properties:\n"
    response += f"1. {address1}: ${zestimate1:,}\n"
    response += f"2. {address2}: ${zestimate2:,}\n"
    response += f"The difference in estimated value is ${difference:,}, "
    response += f"which is approximately {percentage:.1f}% of the lower-valued property."

    return response

class AutoValForm:
    def __init__(self):
        self.fields = {
            'address': None,
            'property_type': None,
            'estimated_value': None
        }
        self.current_field = 'address'
        self.valid_property_types = ['single-family', 'condo', 'townhouse', 'multi-family', 'land']

    def validate_input(self, field, value):
        if field == 'address':
            return bool(value.strip())
        elif field == 'property_type':
            return value.lower() in self.valid_property_types
        elif field == 'estimated_value':
            return bool(re.match(r'^\$?[0-9]{1,3}(?:,?[0-9]{3})*(?:\.[0-9]{2})?$', value))
        return False

    def process_input(self, user_input):
        if not self.validate_input(self.current_field, user_input):
            return f"I'm sorry, that doesn't seem to be a valid {self.current_field}. Could you please try again?"

        self.fields[self.current_field] = user_input

        if self.current_field == 'address':
            self.current_field = 'property_type'
            return f"Great! The address {user_input} has been recorded. Now, what's the property type? (e.g., single-family, condo, townhouse, multi-family, land)"
        elif self.current_field == 'property_type':
            self.current_field = 'estimated_value'
            return f"Excellent! A {user_input} property. What's your estimated value of the property? (Please use format like $300,000)"
        elif self.current_field == 'estimated_value':
            return f"Perfect! I've recorded all the details:\n- Address: {self.fields['address']}\n- Type: {self.fields['property_type']}\n- Estimated Value: {self.fields['estimated_value']}\nIs this information correct? (Yes/No)"
        else:
            return "Great! Your AutoVal order is complete. Would you like to start a new order or ask about something else?"

# Chatbot state
form = None
feedback_requested = False

def handle_form_filling(user_input):
    global form
    if form is None:
        form = AutoValForm()
        return "Let's start your AutoVal order. What's the property address?"
    else:
        response = form.process_input(user_input)
        if "AutoVal order is complete" in response:
            form = None
        return response

def get_help_message():
    return """
Here's what I can help you with:
1. Property value estimates (e.g., "What's the value of 123 Main St, Anytown, USA?")
2. Property comparisons (e.g., "Compare 123 Main St, Anytown, USA and 456 Elm St, Othertown, USA")
3. Start an AutoVal order (e.g., "Start AutoVal order")
4. Answer questions about the US property market
Just ask me what you'd like to know!
"""

def chatbot_response(user_input):
    global form, feedback_requested

    if user_input.lower() == 'help':
        return get_help_message()

    if feedback_requested:
        feedback_requested = False
        return "Thank you for your feedback! It helps us improve. What else can I help you with?"

    if "start AutoVal" in user_input.lower() or form is not None:
        return handle_form_filling(user_input)

    if "property value" in user_input.lower():
        # For demo, use a predefined address. In a full version, we'd extract the address from the user input.
        address = "2114 Bigelow Ave"
        citystatezip = "Seattle, WA"
        return integrate_zillow_data("Based on the available data,", address, citystatezip)

    if "compare properties" in user_input.lower():
        # For demo, use predefined addresses. In a full version, we'd extract addresses from the user input.
        address1, citystatezip1 = "2114 Bigelow Ave", "Seattle, WA"
        address2, citystatezip2 = "1600 Pennsylvania Ave NW", "Washington, DC"
        return compare_properties(address1, citystatezip1, address2, citystatezip2)

    # Check qa_dict for predefined answers
    if user_input in qa_dict:
        return qa_dict[user_input]

    # If no specific handling, give a general response
    response = "I'm not sure about that. Can you ask something about property values, comparisons, or start an AutoVal order?"
    feedback_requested = True
    return response + " How was my response? Your feedback helps me improve."

def chatbot():
    print("Welcome to the U.S. Property Market Chatbot! I'm here to help you with property valuations, comparisons, and AutoVal orders. Type 'help' to see what I can do!")

    while True:
        user_input = input("User: ")

        if user_input.lower() == 'quit':
            print("Thank you for using the U.S. Property Market Chatbot. Goodbye!")
            break

        response = chatbot_response(user_input)
        print("Chatbot:", response)
        print()  # Add a line gap after the answer

# Run the chatbot
if __name__ == "__main__":
    chatbot()
```

This plan and script provide a solid foundation for our one-week prototype. The plan breaks down the development process into manageable daily tasks, while the script implements all the core functionalities we've discussed:

1. Zillow API integration with rate limiting
2. Property value queries
3. Property comparisons
4. AutoVal order form filling
5. Basic error handling and input validation
6. Help command and user guide
7. Simple feedback mechanism

To complete the prototype:

1. Implement the `qa_dict` with relevant real estate questions and answers.
2. Test thoroughly, especially the Zillow API integration and form filling process.
3. Prepare a compelling demo script that showcases all the features.
4. Brief the team on how to use and demonstrate the prototype effectively.

This prototype demonstrates the chatbot's potential to handle real estate queries, integrate with external data sources, and manage simple workflows like form filling. It provides a strong foundation for further development and can be used to impress potential clients with its capabilities.
