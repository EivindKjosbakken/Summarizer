import os
from dotenv import load_dotenv
load_dotenv()
from google.cloud import firestore
db = firestore.Client.from_service_account_json("firestore-key.json")


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