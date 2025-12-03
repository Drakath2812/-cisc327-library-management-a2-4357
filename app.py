"""
Main Flask application entry point for the Library Management System.

This module provides the application factory pattern for creating Flask app instances.
Routes are organized in separate blueprint modules in the routes package.
"""

from flask import Flask
from database import init_database, add_sample_data
from routes import register_blueprints
import argparse
import os

def create_app(test_mode=False):
    """
    Application factory function to create and configure Flask app.
    
    Returns:
        Flask: Configured Flask application instance
    """

    # Select database filename based on mode
    if test_mode:
        db_path = "test_library.db"
        print("[TEST MODE] Using test database:", db_path)

        # Always start from a clean database in test mode
        if os.path.exists(db_path):
            os.remove(db_path)
    else:
        db_path = "library.db"

    os.environ["LIBRARY_DB_PATH"] = db_path

    app = Flask(__name__)
    app.secret_key = "super secret key"
    
    # Initialize the database
    init_database()
    
    # Add sample data for testing and demonstration
    add_sample_data()
    
    # Register all route blueprints
    register_blueprints(app)
    
    return app


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Run the app in test mode with test database.")
    args = parser.parse_args()

    if args.test:
        targetPort = 2812
    else:
        targetPort = 5000

    app = create_app(test_mode=args.test)
    app.run(debug=True, host='0.0.0.0', port=targetPort)
