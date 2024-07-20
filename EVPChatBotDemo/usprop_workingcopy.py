import torch
from transformers import DistilBertTokenizer, DistilBertForQuestionAnswering
from qa_data import qa_dict
import transformers

# Suppress warnings about weight initialization
transformers.logging.set_verbosity_error()

# Load the pre-trained DistilBERT model and tokenizer
model = DistilBertForQuestionAnswering.from_pretrained('distilbert-base-uncased')
tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')

def answer_question(question, context):
    """
    Function to generate an answer for a given question using a pre-trained DistilBERT model.
    
    Args:
        question (str): The question to be answered.
        context (str): The context in which the question is asked.
    
    Returns:
        str: The generated answer.
    """
    # Tokenize the question and context
    inputs = tokenizer(question, context, return_tensors='pt')
    
    # Get the model's predictions
    with torch.no_grad():
        outputs = model(**inputs)
        start_scores = outputs.start_logits
        end_scores = outputs.end_logits
        
    # Find the most likely answer span
    answer_start = torch.argmax(start_scores)
    answer_end = torch.argmax(end_scores) + 1
    answer = tokenizer.convert_tokens_to_string(tokenizer.convert_ids_to_tokens(inputs['input_ids'][0][answer_start:answer_end]))
    
    return answer.strip()

def chatbot():
    """
    Main function to run the chatbot. It interacts with the user and provides answers based on predefined questions or generates answers using a pre-trained model.
    """
    print(" **** Hello! Welcome to the Waivit Chatbot! Ready to explore the US property market? Let's get started! ****")
    print(" -> -> -> -> -> Have AUTOVAL questions? I've got the answers you need. Let's get started! :) ")
    
    while True:
        print("-" * 40)  # Print a line before user input
        user_input = input("User: ")
        print()  # Add a line gap after user input
        
        if user_input.lower() == 'quit':
            print("Thank you for using the US property market Chatbot. Goodbye!")
            break
        
        # Check if the user's question matches any predefined questions
        if user_input in qa_dict:
            answer = qa_dict[user_input]
        else:
            # If no match is found, use the pre-trained model to generate an answer
            # Note: Since context is empty, we handle it gracefully
            context = "This is a placeholder context as the model requires some context to generate an answer."
            answer = answer_question(user_input, context)
        
        # Print the answer
        print("Chatbot:", answer)
        print()  # Add a line gap after the answer
        print("-" * 40)  # Print a line after the answer
        # Print a catchy prompt for the next question
        print("What else would you like to know about the US property market? I'm here to help!")

# Run the chatbot
chatbot()
