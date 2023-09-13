# # Create a virtual environment
# python3 -m venv venv

# # Activate the virtual environment
# source venv/bin/activate

# Install the dependencies
pip install -r requirements.txt

# Run the application
export FLASK_APP=app.py

flask run
