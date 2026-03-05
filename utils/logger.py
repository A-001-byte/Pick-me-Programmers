import logging

def get_logger(name="RiskEngine"):
    """
    Returns a simple, configured logger for tracking system operations.
    """
    logger = logging.getLogger(name)
    
    # Prevent adding multiple handlers if the logger already exists
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        
        # Create console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Add formatter to console handler
        ch.setFormatter(formatter)
        
        # Add console handler to logger
        logger.addHandler(ch)
        
    return logger
