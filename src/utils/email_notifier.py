"""
Email notification utilities.
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailNotifier:
    """Email notification class for sending trade alerts."""
    
    def __init__(self, sender_email, sender_password, recipient_email, smtp_server, smtp_port):
        """
        Initialize email notifier.
        
        Args:
            sender_email (str): Sender email address
            sender_password (str): Sender email password
            recipient_email (str): Recipient email address
            smtp_server (str): SMTP server address
            smtp_port (int): SMTP server port
        """
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.recipient_email = recipient_email
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
    
    def send_email(self, subject, body):
        """
        Send an email.
        
        Args:
            subject (str): Email subject
            body (str): Email body
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart()
            message["From"] = self.sender_email
            message["To"] = self.recipient_email
            message["Subject"] = subject
            
            # Add body to email
            message.attach(MIMEText(body, "plain"))
            
            # Connect to server and send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, self.recipient_email, message.as_string())
            
            logger.info(f"Email sent successfully: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False
    
    def send_trade_notification(self, trade_type, symbol, side, amount, price, stop_loss=None, take_profit1=None, take_profit2=None):
        """
        Send a trade notification email.
        
        Args:
            trade_type (str): Type of trade ('OPEN', 'CLOSE')
            symbol (str): Trading symbol
            side (str): Order side ('buy', 'sell')
            amount (float): Order amount
            price (float): Order price
            stop_loss (float, optional): Stop loss price
            take_profit1 (float, optional): Take profit 1 price
            take_profit2 (float, optional): Take profit 2 price
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        side_formatted = side.upper()
        
        # Format subject
        subject = f"Trading Bot Alert: {trade_type} {side_formatted} Order - {symbol}"
        
        # Format body
        body = f"Trade Alert: {trade_type} {side_formatted} Order\n\n"
        body += f"Date & Time: {timestamp}\n"
        body += f"Symbol: {symbol}\n"
        body += f"Side: {side_formatted}\n"
        body += f"Amount: {amount}\n"
        body += f"Price: {price}\n"
        
        if stop_loss:
            body += f"Stop Loss: {stop_loss}\n"
        
        if take_profit1:
            body += f"Take Profit 1: {take_profit1}\n"
        
        if take_profit2:
            body += f"Take Profit 2: {take_profit2}\n"
        
        body += "\nThis is an automated message from your trading bot."
        
        return self.send_email(subject, body)
    
    def send_error_notification(self, error_message):
        """
        Send an error notification email.
        
        Args:
            error_message (str): Error message
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        subject = "Trading Bot Error Alert"
        body = f"Trading Bot Error Alert\n\n"
        body += f"Date & Time: {timestamp}\n"
        body += f"Error: {error_message}\n\n"
        body += "This is an automated message from your trading bot."
        
        return self.send_email(subject, body) 