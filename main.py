import os
from supabase import create_client, Client

# Replace with your actual Supabase URL and ANON KEY
# You can find the anon key in your Supabase dashboard under Project Settings > API
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://your-project.supabase.co")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "your-anon-key-here")

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