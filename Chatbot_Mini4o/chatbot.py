import json
import re
import logging
from typing import Dict, List, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_data() -> Dict[str, str]:
    """
    Load the dataset from qa_data.py.
    
    Returns:
        Dict[str, str]: A dictionary containing question-answer pairs.
    
    Raises:
        ImportError: If qa_data.py or qa_dict is not found.
        ValueError: If qa_dict is empty or not a dictionary.
    """
    try:
        from qa_data import qa_dict
        if not isinstance(qa_dict, dict) or not qa_dict:
            raise ValueError("qa_dict must be a non-empty dictionary")
        return qa_dict
    except ImportError:
        raise ImportError("Failed to import qa_dict from qa_data.py. Ensure the file exists and is in the correct location.")
    except Exception as e:
        raise Exception(f"An error occurred while loading the data: {str(e)}")

def clean_text(text: str, keep_chars: str = '.?') -> str:
    """
    Clean and normalize text data.
    
    Args:
        text (str): Input text to be cleaned.
        keep_chars (str): Characters to keep in addition to alphanumeric and whitespace.
    
    Returns:
        str: Cleaned and normalized text.
    """
    # Convert to lowercase
    text = text.lower()
    
    # Remove special characters except those specified in keep_chars
    pattern = f'[^\\w\\s{re.escape(keep_chars)}]'
    text = re.sub(pattern, '', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def preprocess_data(data: Dict[str, str]) -> List[Dict[str, str]]:
    """
    Preprocess the dataset by cleaning and formatting the data.
    
    Args:
        data (Dict[str, str]): Raw question-answer pairs.
    
    Returns:
        List[Dict[str, str]]: List of preprocessed question-answer pairs.
    """
    preprocessed_data = []
    
    for question, answer in data.items():
        cleaned_question = clean_text(question)
        cleaned_answer = clean_text(answer)
        
        preprocessed_data.append({
            "question": cleaned_question,
            "answer": cleaned_answer,
            "original_question": question,
            "original_answer": answer
        })
    
    return preprocessed_data

def validate_preprocessed_data(data: List[Dict[str, str]]) -> Tuple[bool, str]:
    """
    Validate the preprocessed data.
    
    Args:
        data (List[Dict[str, str]]): Preprocessed question-answer pairs.
    
    Returns:
        Tuple[bool, str]: A tuple containing a boolean indicating validity and an error message if invalid.
    """
    if not data:
        return False, "Preprocessed data is empty"
    
    required_keys = {"question", "answer", "original_question", "original_answer"}
    
    for item in data:
        if not all(key in item for key in required_keys):
            return False, f"Missing required keys in item: {item}"
        
        if not all(isinstance(item[key], str) for key in required_keys):
            return False, f"Non-string values found in item: {item}"
    
    return True, ""

def format_data_for_gpt(data: List[Dict[str, str]]) -> str:
    """
    Format the preprocessed data for GPT-4o Mini.
    
    Args:
        data (List[Dict[str, str]]): Preprocessed question-answer pairs.
    
    Returns:
        str: JSON-formatted string suitable for GPT-4o Mini.
    """
    formatted_data = {
        "task": "us_property_market_qa",
        "examples": data
    }
    
    return json.dumps(formatted_data, indent=2, ensure_ascii=False)

def save_formatted_data(formatted_data: str, output_file: str = "formatted_data.json") -> None:
    """
    Save the formatted data to a JSON file.
    
    Args:
        formatted_data (str): JSON-formatted string of the data.
        output_file (str): Name of the output file (default: "formatted_data.json").
    
    Raises:
        IOError: If unable to write to the output file.
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(formatted_data)
        logging.info(f"Formatted data saved to {output_file}")
    except IOError:
        raise IOError(f"Failed to write data to {output_file}. Check file permissions and path.")

def main():
    """
    Main function to orchestrate the data loading and preprocessing pipeline.
    """
    try:
        # Step 1: Load the dataset
        logging.info("Loading dataset...")
        raw_data = load_data()
        logging.info(f"Loaded {len(raw_data)} question-answer pairs.")

        # Step 2: Preprocess the data
        logging.info("Preprocessing data...")
        preprocessed_data = preprocess_data(raw_data)
        logging.info(f"Preprocessed {len(preprocessed_data)} question-answer pairs.")

        # Step 3: Validate preprocessed data
        logging.info("Validating preprocessed data...")
        is_valid, error_message = validate_preprocessed_data(preprocessed_data)
        if not is_valid:
            raise ValueError(f"Invalid preprocessed data: {error_message}")
        logging.info("Preprocessed data validated successfully.")

        # Step 4: Format data for GPT-4o Mini
        logging.info("Formatting data for GPT-4o Mini...")
        formatted_data = format_data_for_gpt(preprocessed_data)

        # Step 5: Save formatted data
        save_formatted_data(formatted_data)

        logging.info("Data preprocessing completed successfully.")
        
        # Display a sample of the preprocessed data
        logging.info("Sample of preprocessed data:")
        for item in preprocessed_data[:2]:
            logging.info(json.dumps(item, indent=2, ensure_ascii=False))

    except Exception as e:
        logging.error(f"An error occurred during data preprocessing: {str(e)}")

if __name__ == "__main__":
    main()