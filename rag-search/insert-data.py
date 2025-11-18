import psycopg2
import uuid
from datetime import datetime

def insert_dental_conversation():
    conn = psycopg2.connect(
        dbname="ai_memory",
        user="admin",
        password="xxx",
        host="0.0.0.0",
        port="5434"
    )
    cur = conn.cursor()

    cur.execute("INSERT INTO te_ai_tenant (tnt_name) VALUES (%s) RETURNING tnt_id", ("Dental Clinic",))
    tnt_id = cur.fetchone()[0]

    # 2. Tenant User (Dentist)
    tntu_id = str(uuid.uuid4())
    cur.execute("""
        INSERT INTO te_ai_tenant_user (tntu_id, tntu_tnt_id, tntu_u_id)
        VALUES (%s, %s, %s) RETURNING tntu_id
    """, (tntu_id, tnt_id, 101))

    # 3. Project
    cur.execute("""
        INSERT INTO te_ai_project (pro_tntu_id, pro_title, pro_created)
        VALUES (%s, %s, %s) RETURNING pro_id
    """, (tntu_id, "AI Dental Assistant", datetime.now().time()))
    pro_id = cur.fetchone()[0]

    # 4. Chat
    cur.execute("""
        INSERT INTO te_ai_chat (cht_pro_id, cht_created)
        VALUES (%s, %s) RETURNING cht_id
    """, (pro_id, datetime.now()))
    cht_id = cur.fetchone()[0]

    # 5. Roles
    cur.execute("INSERT INTO te_ai_message_role (msgrole_code, msgrole_display_name) VALUES (%s, %s) RETURNING msgrole_id",
                ("user", "Patient"))
    patient_role = cur.fetchone()[0]

    cur.execute("INSERT INTO te_ai_message_role (msgrole_code, msgrole_display_name) VALUES (%s, %s) RETURNING msgrole_id",
                ("assistant", "Dentist"))
    dentist_role = cur.fetchone()[0]

    # 6. Status
    cur.execute("INSERT INTO te_ai_message_status (msgsts_name) VALUES (%s) RETURNING msgsts_id", ("completed",))
    msgsts_id = cur.fetchone()[0]

    # -------------------
    # MULTIPLE MESSAGES
    # -------------------

    messages = [
    (patient_role, "Doctor, I have severe tooth pain in my lower left molar."),
    (dentist_role, "Sounds like tooth #36 may be infected. When did the pain start?"),
    (patient_role, "It started two days ago, and it hurts when I eat sweets."),
    (dentist_role, "That indicates possible tooth decay. Do you also feel pain while drinking cold water?"),
    (patient_role, "Yes, cold drinks make it worse."),
    (dentist_role, "Alright. Have you taken any painkillers so far?"),
    (patient_role, "Yes, I took ibuprofen, but the pain still comes back."),
    (dentist_role, "Understood. Do you notice any swelling in your gums near that tooth?"),
    (patient_role, "Yes, the gum around the tooth feels swollen."),
    (dentist_role, "This could be an abscess. We may need to do an X-ray."),
    (patient_role, "Okay, can we do that tomorrow morning?"),
    (dentist_role, "Yes, we’ll schedule an X-ray at 10 AM. Are you available then?"),
    (patient_role, "Yes, 10 AM works for me."),
    (dentist_role, "Good. Based on your symptoms, you might need a root canal treatment."),
    (patient_role, "Is root canal painful? I am worried."),
    (dentist_role, "We use local anesthesia, so you won’t feel pain during the procedure."),
    (patient_role, "How long does it take?"),
    (dentist_role, "Usually 1–2 hours depending on complexity. Sometimes two visits are needed."),
    (patient_role, "Okay, please book me for the root canal after the X-ray."),
    (dentist_role, "Done. I have scheduled your X-ray tomorrow and the root canal session afterward."),
]


    message_ids = []
    for role_id, text in messages:
        cur.execute("""
            INSERT INTO te_ai_message (msg_cht_id, msg_msgrole_id, msg_content_text, msg_msgsts_id)
            VALUES (%s, %s, %s, %s) RETURNING msg_id
        """, (cht_id, role_id, text, msgsts_id))
        message_ids.append(cur.fetchone()[0])

    # Canonical Data + Memory for each patient message
    for i, msg_id in enumerate(message_ids):
        cur.execute("""
            INSERT INTO te_ai_canonical_data (
                cantxt_tntu_id, cantxt_type, cantxt_source_id, 
                cantxt_content_text, cantxt_lang, cantxt_n_tokens, cantxt_pii_level, cantxt_srctyp_id
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING cantxt_id
        """, (tntu_id, "text", msg_id, messages[i][1], "en", len(messages[i][1].split()), "low", 1))
        cantxt_id = cur.fetchone()[0]

        if messages[i][0] == patient_role:  # only store facts for patient messages
            cur.execute("""
                INSERT INTO te_ai_memory (mem_tntu_id, mem_pro_id, mem_cht_id, mem_text, mem_type, mem_confidence, mem_source_type)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (tntu_id, pro_id, cht_id, messages[i][1], "patient_note", 0.9, "message"))

    conn.commit()
    print("Inserted dental conversation with multiple messages ✅")

    cur.close()
    conn.close()

if __name__ == "__main__":
    insert_dental_conversation()
