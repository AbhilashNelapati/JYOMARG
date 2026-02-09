from abhi_ai import ABHIAssistant
import sys

print("Initializing Assistant...")
try:
    abhi = ABHIAssistant()
    print("Assistant Initialized.")
    
    domain = "Python Developer"
    print(f"Generating roadmap for {domain}...")
    
    # Call the method directly
    response = abhi.generate_career_roadmap(domain)
    
    print("Response received:")
    print(response)

except Exception as e:
    print(f"CRITICAL MAIN ERROR: {e}")
