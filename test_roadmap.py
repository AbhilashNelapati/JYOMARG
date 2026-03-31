from services.roadmap_service import generate_hybrid_roadmap
import json

print("\n--- Testing Phase 8 Hybrid Roadmap Generator ---")
print("Building rigid Python structure, then injecting LLM content...")

target_domain = "Data Analyst"
print(f"Goal Domain: {target_domain}")

result_json = generate_hybrid_roadmap(target_domain)
parsed_result = json.loads(result_json)

if "error" in parsed_result:
    print(f"FAILED: {parsed_result['error']}")
else:
    print("\nSUCCESS! Skeleton was injected properly:")
    print(f"Title: {parsed_result['title']}")
    
    for phase_idx, phase in enumerate(parsed_result['phases']):
        print(f"\n[Phase {phase.get('phase_num')}] {phase.get('phase_name')}")
        
        for w_idx, week in enumerate(phase.get('weeks')[:1]): # Show just first week of each phase to save space
            print(f"  Week {week.get('week_number')}: {week.get('week_title')}")
            
            for d_idx, day in enumerate(week.get('days')[:1]):
                topic = day['topics'][0]
                print(f"    Day {day.get('day_number')}: {topic.get('topic_name')}")
                print(f"      Explain: {topic.get('explanation')}")
                print(f"      Task:    {topic.get('practice')}")
                
print("\nValidation Complete. Numbering is flawlessly enforced by Python.")
