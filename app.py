import random
import uvicorn
import json
import re
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import PyPDF2
import shutil
from fastapi import FastAPI, Request, Form, Body, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from abhi_ai import ABHIAssistant
from database import init_db, add_user, get_user, get_user_profile, update_user_profile, add_notification, get_notifications, mark_notifications_read, migrate_notifications_schema, migrate_users_schema, add_resume, get_user_resumes, delete_resume, set_active_resume, get_active_resume_text, create_course, get_user_courses, get_course_details, save_day_content, get_day_content, update_course_progress, save_roadmap, get_user_roadmap, delete_roadmap

# Initialize Database
init_db()

app = FastAPI()

# Session Secret Key - దీనివల్ల యూజర్ లాగిన్ వివరాలు భద్రంగా ఉంటాయి
app.add_middleware(SessionMiddleware, secret_key="JYOMARG_ULTRA_SECRET")

# Static files & Templates mapping
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates") 

# ABHI AI instance
abhi = ABHIAssistant()

# --- Page Routes ---

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    user = request.session.get("user")
    if not user: 
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

@app.get("/tutor")
async def tutor_page(request: Request):
    user = request.session.get("user")
    if not user: return RedirectResponse(url="/login")
    return templates.TemplateResponse("TutorAI.html", {"request": request, "user": user})

@app.get("/abhi")
async def abhi_chat_page(request: Request):
    user = request.session.get("user")
    if not user: return RedirectResponse(url="/login")
    return templates.TemplateResponse("AbhiChat.html", {"request": request, "user": user})

@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    if not request.session.get("user"): return RedirectResponse(url="/login")
    
    # Fetch full profile details
    user_email = request.session["user"]["email"]
    user_data = get_user_profile(user_email)
    
    # Check for notifications, if none, generate them
    notifications = get_notifications(user_email)
    
    if not notifications and user_data:
        # Generate initial batch
        user_profile_dict = dict(user_data) # Convert Row to dict
        alerts_json = abhi.generate_job_alerts(user_profile_dict)
        try:
            alerts = json.loads(alerts_json)
            for alert in alerts:
                add_notification(
                    user_email, 
                    alert.get("job_title", "Unknown Role"), 
                    alert.get("company", "Unknown Company"), 
                    alert.get("match_score", 0), 
                    alert.get("reason", "Profile Match"),
                    alert.get("apply_link", "#")
                )
            # Refresh notifications after generation
            notifications = get_notifications(user_email)
        except:
            pass # Fail silently if AI error
            
    # Fetch Resumes
    resumes = get_user_resumes(user_email)
    
    # MIGRATION: If no resumes in table but user has legacy resume_path, migrate it
    if not resumes and user_data and user_data['resume_path']:
        try:
             # Create a dummy filename if not stored, or extract from path
             legacy_path = user_data['resume_path']
             filename = os.path.basename(legacy_path)
             if not filename: filename = "Legacy_Resume.pdf"
             
             # Read text if possible, or leave empty
             try:
                legacy_text = user_data['resume_text'] if 'resume_text' in user_data.keys() else ""
             except:
                legacy_text = ""
             
             # Add to resumes table as ACTIVE
             add_resume(user_email, filename, legacy_path, legacy_text, is_active=True)
             
             # Refresh list
             resumes = get_user_resumes(user_email)
             print(f"Migrated legacy resume for {user_email}")
        except Exception as e:
            print(f"Migration Error: {e}")

    return templates.TemplateResponse("profile.html", {"request": request, "user": user_data, "notifications": notifications, "resumes": resumes})

@app.get("/api/notifications")
async def get_notifications_api(request: Request):
    user_session = request.session.get("user")
    if not user_session: return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    notifications = get_notifications(user_session["email"])
    # Convert Row objects to dicts
    notifs_list = [dict(row) for row in notifications]
    return JSONResponse(notifs_list)

@app.post("/api/notifications/search")
async def trigger_search_custom(request: Request):
    user_session = request.session.get("user")
    if not user_session: return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    email = user_session["email"]
    user_data = get_user_profile(email)
    
    if not user_data:
        return JSONResponse({"error": "Profile not found"}, status_code=404)
        
    try:
        # Check for active resume to augment profile
        active_text = get_active_resume_text(email)
        user_profile_dict = dict(user_data)
        if active_text:
             user_profile_dict['resume_text'] = active_text
             
        alerts_json = abhi.generate_job_alerts(user_profile_dict)
        alerts = json.loads(alerts_json)
        
        count = 0
        for alert in alerts:
            add_notification(email, alert.get("job_title"), alert.get("company"), alert.get("match_score"), alert.get("reason"), alert.get("apply_link"))
            count += 1
            
        return JSONResponse({"message": f"Search complete. Found {count} new jobs."})
    except Exception as e:
        print(f"Manual Search Error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/resume")
async def resume_page(request: Request):
    user = request.session.get("user")
    if not user: return RedirectResponse(url="/login")
    return templates.TemplateResponse("ResumeBuilder.html", {"request": request, "user": user})

@app.get("/analyzer")
async def analyzer_page(request: Request):
    user = request.session.get("user")
    if not user: return RedirectResponse(url="/login")
    return templates.TemplateResponse("SkillAnalyzer.html", {"request": request, "user": user})

@app.get("/career-architect")
async def career_architect_page(request: Request):
    user = request.session.get("user")
    if not user: return RedirectResponse(url="/login")
    return templates.TemplateResponse("CareerArchitect.html", {"request": request, "user": user})

@app.post("/api/career/roadmap/generate")
async def generate_roadmap_api(request: Request):
    """
    Generates a roadmap AND saves it (Legacy/CareerArchitect behavior).
    Or can be used with ?save=false for preview?
    Let's keep this as the "Generate and output" endpoint, maybe add a save param.
    Actually, to support the separate 'Save' button, we should allow generating without saving.
    """
    user = request.session.get("user")
    if not user: return JSONResponse({"error": "Unauthorized"}, 401)
    
    data = await request.json()
    domain = data.get("domain")
    preview = data.get("preview", False) # New flag
    
    # Generate Roadmap via AI
    roadmap_json = abhi.generate_career_roadmap(domain)
    
    if preview:
        try:
            return JSONResponse(json.loads(roadmap_json))
        except json.JSONDecodeError:
            # Return raw text as error for debugging
            return JSONResponse({"error": f"Invalid AI Response: {roadmap_json[:500]}"}, 500)
    
    # Save to DB (Default behavior)
    try:
        if save_roadmap(user["email"], domain, roadmap_json):
            return JSONResponse(json.loads(roadmap_json))
        else:
            return JSONResponse({"error": "Failed to save roadmap"}, 500)
    except json.JSONDecodeError:
         return JSONResponse({"error": f"Invalid AI Response: {roadmap_json[:500]}"}, 500)

@app.post("/api/career/roadmap/save")
async def save_roadmap_endpoint(request: Request):
    """
    Saves a provided roadmap JSON to the DB.
    """
    user = request.session.get("user")
    if not user: return JSONResponse({"error": "Unauthorized"}, 401)
    
    data = await request.json()
    domain = data.get("domain")
    roadmap_data = data.get("roadmap") # The full JSON object
    
    if not domain or not roadmap_data:
        return JSONResponse({"error": "Missing domain or roadmap data"}, 400)
    
    roadmap_json_str = json.dumps(roadmap_data)
    
    if save_roadmap(user["email"], domain, roadmap_json_str):
        return JSONResponse({"success": True})
    else:
        return JSONResponse({"error": "Failed to save roadmap"}, 500)

@app.post("/api/career/roadmap/delete") # Using POST for simplicity with existing client fetch
async def delete_roadmap_endpoint(request: Request):
    """
    Deletes the current user's roadmap.
    """
    user = request.session.get("user")
    if not user: return JSONResponse({"error": "Unauthorized"}, 401)
    
    if delete_roadmap(user["email"]):
        return JSONResponse({"success": True})
    else:
        return JSONResponse({"error": "Failed to delete roadmap"}, 500)

@app.get("/api/career/roadmap")
async def get_roadmap_api(request: Request):
    user = request.session.get("user")
    if not user: return JSONResponse({"error": "Unauthorized"}, 401)
    
    roadmap = get_user_roadmap(user["email"])
    if roadmap:
        return JSONResponse({
            "domain": roadmap["domain"],
            "roadmap": json.loads(roadmap["roadmap_json"]),
            "created_at": roadmap["created_at"]
        })
    else:
        return JSONResponse(None)

# --- Email Function ---
# --- Email Function Removed ---

# --- Authentication Logic (Signup/Login) ---

@app.post("/auth/signup")
async def handle_signup(request: Request, full_name: str = Form(...), email: str = Form(...), password: str = Form(...), confirm_password: str = Form(...)):
    # Password Security Validation
    if len(password) < 8:
        return "Error: Password must be at least 8 characters."
    if not re.search(r"[A-Z]", password) or not re.search(r"[0-9]", password) or not re.search(r"[!@#$%^&*]", password):
        return "Error: Password must have 1 Capital, 1 Number, and 1 Symbol."
    
    if password != confirm_password:
        return "Error: Passwords do not match."

    # Direct Add to DB
    if add_user(full_name, email, password):
         return RedirectResponse(url="/login", status_code=303)
    else:
         return "Error: Email already registered."

@app.post("/auth/login")
async def handle_login(request: Request, email: str = Form(...), password: str = Form(...)):
    user = get_user(email, password)

    if user:
        request.session["user"] = {"name": user[0], "email": user[1]}
        return RedirectResponse(url="/dashboard", status_code=303)
    else:
        return "Invalid Credentials. <a href='/login'>Try Again</a>"

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")

# --- Resume Management Routes ---

# Helper for Triggering AI Job Search
async def trigger_job_search(email):
    try:
        user_data = get_user_profile(email)
        if user_data:
            # Get NEW active text
            active_text = get_active_resume_text(email)
            
            # Update user profile dict with specific active resume text for AI
            user_profile_dict = dict(user_data)
            user_profile_dict['resume_text'] = active_text 
            
            alerts_json = abhi.generate_job_alerts(user_profile_dict)
            alerts = json.loads(alerts_json)
            for alert in alerts:
                add_notification(email, alert.get("job_title"), alert.get("company"), alert.get("match_score"), alert.get("reason"), alert.get("apply_link"))
            print(f"DEBUG: Job Search Triggered for {email}")
            return True
    except Exception as e:
        print(f"Activation Search Error: {e}")
        return False

@app.post("/api/resumes/upload")
async def upload_resume_api(request: Request, resume: UploadFile = File(...)):
    user_session = request.session.get("user")
    if not user_session: return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    email = user_session["email"]
    try:
        if not resume.filename.endswith(".pdf"):
            return JSONResponse({"error": "Only PDF files are allowed"}, status_code=400)

        upload_dir = "static/uploads/resumes"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save File
        filename = f"{email}_{int(os.path.getmtime(upload_dir) if os.path.exists(upload_dir) else 0)}_{resume.filename}" 
        file_path = f"{upload_dir}/{filename}"
        
        print(f"DEBUG: Saving resume to {file_path}")
        with open(file_path, "wb+") as file_object:
            shutil.copyfileobj(resume.file, file_object)
        print("DEBUG: File saved successfully")
            
        # Parse Text
        resume_text = ""
        try:
            print(f"DEBUG: Parsing PDF from {file_path}")
            reader = PyPDF2.PdfReader(file_path)
            for page in reader.pages:
                resume_text += page.extract_text()
            print(f"DEBUG: PDF parsed, length: {len(resume_text)}")
        except Exception as e:
             print(f"DEBUG: PDF Parse Error: {e}")
             # Continue even if parse fails, just to save the file
             
        # Determine if should be active
        existing_resumes = get_user_resumes(email)
        is_active = len(existing_resumes) == 0
        print(f"DEBUG: Adding to DB, is_active={is_active}")
        
        if add_resume(email, resume.filename, "/" + file_path, resume_text, is_active):
            print("DEBUG: Resume added to DB")
            if is_active:
                 # Trigger Search if active
                 await trigger_job_search(email)

            return JSONResponse({"message": "Resume uploaded successfully", "filename": resume.filename})
        else:
            print("DEBUG: DB Error during add_resume")
            return JSONResponse({"error": "Database error"}, status_code=500)

    except Exception as e:
        print(f"Resume Upload Error: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/resumes/delete")
async def delete_resume_api(request: Request):
    user_session = request.session.get("user")
    if not user_session: return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    data = await request.json()
    resume_id = data.get("id")
    
    if delete_resume(resume_id, user_session["email"]):
        return JSONResponse({"message": "Deleted"})
    return JSONResponse({"error": "Failed"}, status_code=500)

@app.post("/api/resumes/activate")
async def activate_resume_api(request: Request):
    user_session = request.session.get("user")
    if not user_session: return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    data = await request.json()
    resume_id = data.get("id")
    
    if set_active_resume(resume_id, user_session["email"]):
        # Trigger Search
        await trigger_job_search(user_session["email"])
        return JSONResponse({"message": "Activated and Search Started"})
    return JSONResponse({"error": "Failed"}, status_code=500)
    
# --- End Resume Management Routes ---

@app.post("/profile/update")
async def update_profile(
    request: Request,
    phone: str = Form(""),
    location: str = Form(""),
    bio: str = Form(""),
    linkedin: str = Form(""),
    github: str = Form(""),
    skills: str = Form(""),
    experience_years: str = Form(""),
    degree: str = Form(""),
    university: str = Form(""),
    grad_year: str = Form("")
):
    user_session = request.session.get("user")
    if not user_session: return RedirectResponse(url="/login")

    email = user_session["email"]
    
    # Legacy update (keep for non-resume fields)
    if update_user_profile(email, phone, location, bio, linkedin, github, skills, experience_years, degree, university, grad_year):
        return RedirectResponse(url="/profile?saved=true", status_code=303)
    else:
        return "Error updating profile."

@app.get("/api/notifications")
async def get_notifications_api(request: Request):
    user_session = request.session.get("user")
    if not user_session: return JSONResponse({"notifications": []})
    
    email = user_session["email"]
    notifications = get_notifications(email)
    
    # Convert Row objects to dicts
    notif_list = []
    for n in notifications:
        notif_list.append({
            "job_title": n["job_title"],
            "company": n["company"],
            "match_score": n["match_score"],
            "reason": n["reason"],
            "apply_link": n["apply_link"],
            "created_at": n["created_at"],
            "is_read": n["is_read"]
        })
        
    return JSONResponse({"notifications": notif_list})

@app.post("/api/notifications/read")
async def mark_read_api(request: Request):
    user_session = request.session.get("user")
    if user_session:
        mark_notifications_read(user_session["email"])
    return JSONResponse({"status": "success"})

@app.post("/analyze-gap")
async def analyze_gap_endpoint(data: dict = Body(...)):
    resume = data.get("resume_text", "")
    jd = data.get("jd_text", "")
    raw_ai_response = abhi.analyze_skill_gap(resume, jd)
    try:
        clean_json = raw_ai_response.replace("```json", "").replace("```", "").strip()
        parsed_json = json.loads(clean_json)
        return JSONResponse(content=parsed_json)
    except:
        return JSONResponse(content={"match_score": 0, "skill_scores": {}, "missing_skills": [], "advice": "Error processing AI data."})

@app.post("/ask")
async def ask_abhi(query: str = Form(...)):
    response_text = abhi.ask_abhi(query)
    return JSONResponse(content={"response": response_text})

@app.post("/generate-resume")
async def generate_resume_endpoint(data: dict = Body(...)):
    prompt = f"Architect a professional resume for {data['name']} based on this data: {data['existing_resume']} optimized for this JD: {data['job_desc']}"
    result = abhi.ask_abhi(prompt)
    return {"resume_content": result}

# --- LEARN Feature Routes ---

@app.get("/learn", response_class=HTMLResponse)
async def learn_page(request: Request):
    if not request.session.get("user"): return RedirectResponse(url="/login")
    return templates.TemplateResponse("learn.html", {"request": request, "user": request.session["user"]})

@app.get("/api/learn/courses")
async def get_courses_api(request: Request):
    user = request.session.get("user")
    if not user: return JSONResponse({"error": "Unauthorized"}, 401)
    courses = get_user_courses(user["email"])
    return JSONResponse([dict(c) for c in courses])

@app.post("/api/learn/generate")
async def generate_course_api(request: Request):
    user = request.session.get("user")
    if not user: return JSONResponse({"error": "Unauthorized"}, 401)
    
    data = await request.json()
    topic = data.get("topic")
    
    # Generate Syllabus via AI
    syllabus_json = abhi.generate_course_syllabus(topic)
    
    # Create in DB
    course_id = create_course(user["email"], topic, syllabus_json)
    
    if course_id:
        return JSONResponse({"message": "Course created", "id": course_id})
    return JSONResponse({"error": "Failed to create course"}, 500)

@app.get("/api/learn/course/{course_id}")
async def get_course_details_api(request: Request, course_id: int):
    user = request.session.get("user")
    if not user: return JSONResponse({"error": "Unauthorized"}, 401)
    
    course = get_course_details(course_id)
    if not course: return JSONResponse({"error": "Not found"}, 404)
    
    return JSONResponse(dict(course))

@app.get("/api/learn/course/{course_id}/content")
async def get_day_content_api(request: Request, course_id: int):
    week = int(request.query_params.get("week"))
    day = int(request.query_params.get("day"))
    title = request.query_params.get("title")
    
    # Check Cache
    content = get_day_content(course_id, week, day)
    
    if not content:
        # Generate via AI
        course = get_course_details(course_id)
        content = abhi.generate_day_content(course["topic"], title)
        save_day_content(course_id, week, day, content)
        
    return JSONResponse({"content": content})

@app.post("/api/learn/course/{course_id}/progress")
async def update_progress_api(request: Request, course_id: int):
    data = await request.json()
    week = data.get("week")
    day = data.get("day")
    completed_days = json.dumps(data.get("completed_days")) # Store as JSON string
    
    update_course_progress(course_id, week, day, completed_days)
    return JSONResponse({"message": "Progress updated"})

@app.get("/api/learn/course/{course_id}/quiz")
async def get_quiz_api(request: Request, course_id: int):
    week = int(request.query_params.get("week"))
    is_final = request.query_params.get("final") == "true"
    
    course = get_course_details(course_id)
    quiz_json = abhi.generate_assessment(course["topic"], week, is_final)
    
    return JSONResponse(json.loads(quiz_json))

@app.post("/api/learn/course/{course_id}/quiz/submit")
async def submit_quiz_api(request: Request, course_id: int):
    data = await request.json()
    passed = data.get("passed")
    week = data.get("week")
    
    if passed:
        # Unlock logic handled on frontend or strictly here? 
        # For now, frontend handles logic, backend just acknowledges.
        pass
        
    return JSONResponse({"message": "Quiz submitted", "unlocked": passed})

# Revert port change if necessary, keeping it standard 8000 for now or user's preference
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=9000)

