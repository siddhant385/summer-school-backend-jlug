import os
from supabase import create_client, Client

# Replace with your actual Supabase URL and ANON KEY
# You can find the anon key in your Supabase dashboard under Project Settings > API
SUPABASE_URL = "https://bsognxaxkgtqyxoymmpp.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJzb2dueGF4a2d0cXl4b3ltbXBwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQxMDgyNjYsImV4cCI6MjA2OTY4NDI2Nn0.IBLjDjFIdHzHxwsilNEjAqpC9FdUHbrByKzuUcIzD5A" # Use the public anon key for this

# Your existing user's details
test_email = "test@example.com"
# Make sure this is the correct password for your existing user
test_password = "123456"

print("Attempting to sign in and get JWT...")

# Initialize the Supabase Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

try:
    # Sign in as the existing user
    session_response = supabase.auth.sign_in_with_password({
        "email": test_email,
        "password": test_password
    })

    # Extract and print the JWT (access token)
    jwt_token = session_response.session.access_token
    print("\n✅ SUCCESS! Your test JWT is below:\n")
    print(jwt_token)

except Exception as e:
    print(f"\n❌ FAILED to sign in and get token: {e}")
    print("\nPlease double-check if the email and password are correct.")