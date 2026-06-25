from dotenv import load_dotenv
import os

load_dotenv()

def check_var(name):
    value = os.getenv(name)
    print(f"{name}: {'✅ Set' if value else '❌ Missing'}")
    if value and len(value) > 10:
        print(f"  Sample: {value[:5]}...{value[-5:]}")
    return bool(value)

print("🔍 Verifying .env file...\n")
all_set = True

all_set &= check_var("SUPABASE_URL")
all_set &= check_var("SUPABASE_KEY")
all_set &= check_var("GROQ_API_KEY")
all_set &= check_var("NVIDIA_API_KEY")
all_set &= check_var("CHROMA_DB_PATH")

print(f"\n📋 Status: {'✅ All keys configured' if all_set else '❌ Some keys missing'}")