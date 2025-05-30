import streamlit as st
from mem0 import Memory
import os
import sys
from pathlib import Path
import json
from datetime import datetime, timedelta
from qdrant_client import QdrantClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(str(Path(__file__).parent.parent.resolve()))

from config.appconfig import (
    QDRANT_URL_CLOUD,
    QDRANT_URL_LOCAL,
    QDRANT_API_KEY,
    GROQ_API_KEY,
    GOOGLE_API_KEY,
)
GROQ_MODEL_NAME = "llama-3.3-70b-versatile"
GROQ_MODEL_NAME = "mixtral-8x7b-32768"

config = {
    "llm": {
        "provider": "groq",
        "config": {
            "model": GROQ_MODEL_NAME,
            "api_key": GROQ_API_KEY,
            "temperature": 0.1,
            "max_tokens": 1000,
        }
    }
}

m = Memory.from_config(config)
m.add("Likes to play cricket on weekends", user_id="alice", metadata={"category": "hobbies"})

def generate_synthetic_data(self, user_id: str) -> dict | None:
    try:
        today = datetime.now()
        order_date = (today - timedelta(days=3)).strftime("%d/%m/%Y")
        expected_delivery = (today + timedelta(days=5)).strftime("%d/%m/%Y")

        from groq import Groq
        groq_client = Groq(api_key=GROQ_API_KEY)

        # Nigerian-focused prompt with explicit formatting
        prompt = f"""Generate a detailed Nigerian customer profile for raqibtech customer ID {user_id}.

        Follow this EXACT format:

        CUSTOMER PROFILE
        - Full name: [Common Nigerian name e.g., Adebayo Chukwuma]
        - Phone: [0803... or 0812... number]
        - Email: [@yahoo.com or @gmail.com]
        - Location: [Lagos|Abuja|Port Harcourt neighborhood e.g., Victoria Island, Wuse 2]

        CURRENT ORDER (Date: {order_date})
        - Product: [Popular Nigerian electronics e.g., Solar inverter, Thermocool fridge]
        - Price: [₦ followed by amount e.g., ₦150,000]
        - Delivery: [Address with landmark e.g., 24 Oba Akran, beside Chicken Republic]
        - Expected Delivery: {expected_delivery}

        ORDER HISTORY (LAST 3 MONTHS)
        - [Month]: [Product] - [Price]
        - [Month]: [Product] - [Price]

        CUSTOMER PREFERENCES
        - Payment: [Bank transfer|Opay|Palmpay]
        - Delivery note: [Nigerian-specific instruction e.g., "Call okada rider before coming"]

        Use Nigerian English terms like "NEPA bill", "okada", or "pure water".
        Do NOT use markdown or special formatting.
        """

        response = groq_client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a Nigerian e-commerce data generator. Use common Nigerian formats and pidgin where appropriate."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=800
        )

        raw_content = response.choices[0].message.content

        # Enhanced parsing with Nigerian context validation
        required_sections = {
            "CUSTOMER PROFILE": ["Full name", "Phone", "Email", "Location"],
            "CURRENT ORDER": ["Product", "Price", "Delivery"],
            "ORDER HISTORY": [],
            "CUSTOMER PREFERENCES": ["Payment"]
        }

        parsed_data = {}
        current_section = None

        for line in raw_content.split('\n'):
            line = line.strip()
            if line.startswith("CUSTOMER PROFILE"):
                current_section = "CUSTOMER PROFILE"
                parsed_data[current_section] = {}
            elif line.startswith("CURRENT ORDER"):
                current_section = "CURRENT ORDER"
                parsed_data[current_section] = {}
            elif line.startswith("ORDER HISTORY"):
                current_section = "ORDER HISTORY"
                parsed_data[current_section] = []
            elif line.startswith("CUSTOMER PREFERENCES"):
                current_section = "CUSTOMER PREFERENCES"
                parsed_data[current_section] = {}
            elif line.startswith("-") and current_section:
                if current_section == "ORDER HISTORY":
                    parsed_data[current_section].append(line[1:].strip())
                else:
                    key_value = line[1:].strip().split(":", 1)
                    if len(key_value) == 2:
                        key = key_value[0].strip()
                        value = key_value[1].strip()
                        parsed_data[current_section][key] = value

        # Nigerian-specific validation
        errors = []
        if not parsed_data.get("CUSTOMER PROFILE", {}).get("Phone", "").startswith(("080", "081", "070", "090")):
            errors.append("Invalid Nigerian phone number format")

        if "₦" not in parsed_data.get("CURRENT ORDER", {}).get("Price", ""):
            errors.append("Price missing Naira symbol (₦)")

        if not errors and all(
            section in parsed_data and
            (isinstance(parsed_data[section], dict) and parsed_data[section]) or
            (isinstance(parsed_data[section], list) and len(parsed_data[section]) >= 1)
            for section in required_sections
        ):
            # Store in memory with Nigerian formatting
            profile_text = "\n".join(
                f"{section}\n" + "\n".join(
                    f"- {k}: {v}" if isinstance(v, str) else f"- {item}"
                    for k, v in (data.items() if isinstance(data, dict) else data)
                )
                for section, data in parsed_data.items()
            )

            self.memory.add(
                profile_text,
                user_id=user_id,
                metadata={"app_id": self.app_id, "role": "system"}
            )

            # Display in Streamlit with Nigerian styling
            with st.expander(f"  Customer Profile - {user_id}", expanded=True):
                cols = st.columns(2)
                with cols[0]:
                    st.subheader("Basic Info")
                    st.write(f"**Name**: {parsed_data['CUSTOMER PROFILE']['Full name']}")
                    st.write(f"**Phone**: {parsed_data['CUSTOMER PROFILE']['Phone']}")
                    st.write(f"**Location**: {parsed_data['CUSTOMER PROFILE']['Location']}")

                with cols[1]:
                    st.subheader("Current Order")
                    st.write(f"**Product**: {parsed_data['CURRENT ORDER']['Product']}")
                    st.write(f"**Price**: {parsed_data['CURRENT ORDER']['Price']}")
                    st.write(f"**Delivery**: {parsed_data['CURRENT ORDER']['Delivery']}")

                st.subheader("Order History")
                for item in parsed_data["ORDER HISTORY"]:
                    st.write(f"- {item}")

                st.subheader("Preferences")
                st.write(f"**Payment Method**: {parsed_data['CUSTOMER PREFERENCES']['Payment']}")
                if "Delivery note" in parsed_data["CUSTOMER PREFERENCES"]:
                    st.write(f"**Delivery Note**: {parsed_data['CUSTOMER PREFERENCES']['Delivery note']}")

            return parsed_data
        else:
            error_msg = " | ".join(errors) if errors else "Missing required sections"
            st.error(f"Abeg, something no correct! {error_msg}")
            st.error(f"Raw response: {raw_content[:500]}...")  # Show partial response for debugging
            return None

    except Exception as e:
        st.error(f"Omo, error don occur! {str(e)}")
        st.error("Abeg try again or contact support with code: NG-ERR-007")
        return None

