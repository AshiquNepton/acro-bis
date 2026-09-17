import os
import configparser
import psycopg2
from pathlib import Path

class DatabaseHelper:
    """Helper class for database configuration management"""
    
    CONFIG_FILE = 'db_config.ini'
    
    @staticmethod
    def get_config_path():
        """Get the full path to config file"""
        base_dir = Path(__file__).resolve().parent.parent
        return os.path.join(base_dir, DatabaseHelper.CONFIG_FILE)
    
    @staticmethod
    def is_configured():
        """Check if database is configured"""
        config_path = DatabaseHelper.get_config_path()
        return os.path.exists(config_path)
    
    @staticmethod
    def save_credentials(db_config):
        """
        Save database credentials to config file
        
        Args:
            db_config (dict): Dictionary containing database configuration
                {
                    'engine': 'postgresql',
                    'name': 'database_name',
                    'user': 'username',
                    'password': 'password',
                    'host': 'localhost',
                    'port': '5432'
                }
        """
        config = configparser.ConfigParser()
        config['DATABASE'] = {
            'ENGINE': str(db_config.get('engine', 'postgresql')),
            'NAME': str(db_config.get('name', '')),
            'USER': str(db_config.get('user', '')),
            'PASSWORD': str(db_config.get('password', '')),
            'HOST': str(db_config.get('host', '')),
            'PORT': str(db_config.get('port', '5432'))
        }
        
        config_path = DatabaseHelper.get_config_path()
        with open(config_path, 'w') as configfile:
            config.write(configfile)
    
    @staticmethod
    def load_credentials():
        """
        Load database credentials from config file
        
        Returns:
            dict: Database configuration or None if not found
        """
        config_path = DatabaseHelper.get_config_path()
        
        if not os.path.exists(config_path):
            return None
        
        config = configparser.ConfigParser()
        config.read(config_path)
        
        if 'DATABASE' not in config:
            return None
        
        db_section = config['DATABASE']
        return {
            'ENGINE': db_section.get('ENGINE', 'postgresql'),
            'NAME': db_section.get('NAME', ''),
            'USER': db_section.get('USER', ''),
            'PASSWORD': db_section.get('PASSWORD', ''),
            'HOST': db_section.get('HOST', ''),
            'PORT': db_section.get('PORT', '5432')
        }
    
    @staticmethod
    def test_connection(db_config):
        """
        Test database connection
        
        Args:
            db_config (dict): Database configuration
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # Convert port to integer
            port = int(db_config.get('port', 5432))
            
            # Create connection string
            connection = psycopg2.connect(
                host=db_config.get('host'),
                port=port,
                database=db_config.get('name'),
                user=db_config.get('user'),
                password=db_config.get('password'),
                connect_timeout=10
            )
            
            # Test query
            cursor = connection.cursor()
            cursor.execute('SELECT version();')
            version = cursor.fetchone()
            
            cursor.close()
            connection.close()
            
            return True, f'Connection successful! PostgreSQL version: {version[0][:50]}...'
            
        except psycopg2.OperationalError as e:
            error_msg = str(e)
            if 'could not connect to server' in error_msg:
                return False, 'Could not connect to server. Please check host and port.'
            elif 'authentication failed' in error_msg:
                return False, 'Authentication failed. Please check username and password.'
            elif 'database' in error_msg and 'does not exist' in error_msg:
                return False, 'Database does not exist. Please check database name.'
            else:
                return False, f'Connection error: {error_msg}'
        except ValueError:
            return False, 'Invalid port number. Port must be a number between 1 and 65535.'
        except Exception as e:
            return False, f'Unexpected error: {str(e)}'
    
    @staticmethod
    def get_database_config():
        """
        Get database configuration for Django settings
        
        Returns:
            dict: Database configuration for Django DATABASES setting
        """
        credentials = DatabaseHelper.load_credentials()
        
        if not credentials:
            return {
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': 'db.sqlite3',
                }
            }
        
        return {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': credentials['NAME'],
                'USER': credentials['USER'],
                'PASSWORD': credentials['PASSWORD'],
                'HOST': credentials['HOST'],
                'PORT': credentials['PORT'],
            }
        }
    
    @staticmethod
    def delete_credentials():
        """Delete database configuration file"""
        config_path = DatabaseHelper.get_config_path()
        if os.path.exists(config_path):
            os.remove(config_path)
            return True
        return False