import os
from google.cloud import firestore
import streamlit as st
from dotenv import load_dotenv
load_dotenv()



# Initialize the Firestore client, normally you would do it with firestore-key.json, but I have to store keys in secret.toml, so manually load json object instead
service_account_info = {
    "type": st.secrets["firestore"]["type"],
    "project_id": st.secrets["firestore"]["project_id"],
    "private_key_id": st.secrets["firestore"]["private_key_id"],
    "private_key": st.secrets["firestore"]["private_key"],
    "client_email": st.secrets["firestore"]["client_email"],
    "client_id": st.secrets["firestore"]["client_id"],
    "auth_uri": st.secrets["firestore"]["auth_uri"],
    "token_uri": st.secrets["firestore"]["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["firestore"]["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["firestore"]["client_x509_cert_url"]
}
db = firestore.Client.from_service_account_info(service_account_info)


STANDARD_START_TOKENS = int(os.getenv('STANDARD_START_TOKENS'))


def add_user(db, email, remaining_tokens=STANDARD_START_TOKENS):
	doc_ref = db.collection('users').document(email)
	doc_ref.set({
		'remaining_tokens': remaining_tokens
	})

def get_user(db, email):
	doc_ref = db.collection('users').document(email)
	doc = doc_ref.get()
	if doc.exists:
		return doc.to_dict()
	return None

def add_user_tokens(db, email, tokens):
	doc_ref = db.collection('users').document(email)
	doc = doc_ref.get()
	if doc.exists:
		doc_dict = doc.to_dict()
		doc_ref.update({
			'remaining_tokens': doc_dict['remaining_tokens'] + tokens
		})
		print("Successfully added tokens")
	else: raise ValueError("User does not exist. Did not add tokens")

def subtract_user_tokens(db, email, tokens):
	doc_ref = db.collection('users').document(email)
	doc = doc_ref.get()
	if doc.exists:
		doc_dict = doc.to_dict()
		remaining_tokens = doc_dict['remaining_tokens'] - tokens
		doc_ref.update({
			'remaining_tokens': remaining_tokens
		})
		print("Successfully subtracted tokens")
		return remaining_tokens
	else: raise ValueError("User does not exist. Did not subtract tokens")