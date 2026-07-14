import json
import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.api.schemas.client import (
    ClientCreateRequest,
    ClientStatusUpdate,
    ClientUpdateRequest,
)
from app.models.user_access import Client, ClientContact


def _client_query(db: Session):
    return db.query(Client).options(joinedload(Client.contacts))


def list_clients(db: Session) -> list[Client]:
    return _client_query(db).order_by(Client.created_at.desc()).all()


def get_client(db: Session, client_id: uuid.UUID) -> Client:
    client = _client_query(db).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return client


def create_client(db: Session, payload: ClientCreateRequest) -> Client:
    submission_json = (
        json.dumps([f.model_dump() for f in payload.submission_format])
        if payload.submission_format
        else None
    )

    client = Client(
        company_name=payload.company_name,
        industry=payload.industry,
        location=payload.location,
        website=payload.website,
        company_size=payload.company_size,
        billing_address=payload.billing_address,
        gst_number=payload.gst_number,
        payment_terms=payload.payment_terms,
        portal_url=payload.portal_url,
        submission_format=submission_json,
        status="active",
    )
    db.add(client)
    db.flush()

    for contact_in in payload.contacts:
        db.add(
            ClientContact(
                client_id=client.id,
                name=contact_in.name,
                designation=contact_in.designation,
                email=contact_in.email,
                phone=contact_in.phone,
                linkedin_url=contact_in.linkedin_url,
                primary_contact=contact_in.primary_contact,
            )
        )

    db.commit()
    return _client_query(db).filter(Client.id == client.id).one()


def update_client(db: Session, client_id: uuid.UUID, payload: ClientUpdateRequest) -> Client:
    client = _client_query(db).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    if payload.company_name is not None:
        client.company_name = payload.company_name
    if payload.industry is not None:
        client.industry = payload.industry
    if payload.location is not None:
        client.location = payload.location
    if payload.website is not None:
        client.website = payload.website
    if payload.company_size is not None:
        client.company_size = payload.company_size
    if payload.billing_address is not None:
        client.billing_address = payload.billing_address
    if payload.gst_number is not None:
        client.gst_number = payload.gst_number
    if payload.payment_terms is not None:
        client.payment_terms = payload.payment_terms
    if payload.portal_url is not None:
        client.portal_url = payload.portal_url
    if payload.submission_format is not None:
        client.submission_format = json.dumps([f.model_dump() for f in payload.submission_format])

    if payload.contacts is not None:
        incoming_ids = {c.id for c in payload.contacts if c.id is not None}
        existing_map = {c.id: c for c in client.contacts}

        # Delete contacts not present in the incoming payload
        for existing_id, existing_contact in existing_map.items():
            if existing_id not in incoming_ids:
                db.delete(existing_contact)

        for contact_in in payload.contacts:
            if contact_in.id and contact_in.id in existing_map:
                # Update in place
                existing = existing_map[contact_in.id]
                existing.name = contact_in.name
                existing.designation = contact_in.designation
                existing.email = contact_in.email
                existing.phone = contact_in.phone
                existing.linkedin_url = contact_in.linkedin_url
                existing.primary_contact = contact_in.primary_contact
            else:
                # Insert new
                db.add(
                    ClientContact(
                        client_id=client.id,
                        name=contact_in.name,
                        designation=contact_in.designation,
                        email=contact_in.email,
                        phone=contact_in.phone,
                        linkedin_url=contact_in.linkedin_url,
                        primary_contact=contact_in.primary_contact,
                    )
                )

    db.commit()
    return _client_query(db).filter(Client.id == client_id).one()


def update_client_status(db: Session, client_id: uuid.UUID, payload: ClientStatusUpdate) -> Client:
    client = _client_query(db).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    client.status = payload.status
    db.commit()
    return _client_query(db).filter(Client.id == client_id).one()


def serialize_client(client: Client) -> dict:
    submission: list | None = None
    if client.submission_format:
        try:
            submission = json.loads(client.submission_format)
        except (json.JSONDecodeError, TypeError):
            submission = []

    contacts = [
        {
            "id": c.id,
            "name": c.name,
            "designation": c.designation,
            "email": c.email,
            "phone": c.phone,
            "linkedin_url": c.linkedin_url,
            "primary_contact": c.primary_contact,
        }
        for c in client.contacts
    ]

    return {
        "id": client.id,
        "company_name": client.company_name,
        "industry": client.industry,
        "location": client.location,
        "website": client.website,
        "company_size": client.company_size,
        "billing_address": client.billing_address,
        "gst_number": client.gst_number,
        "payment_terms": client.payment_terms,
        "portal_url": client.portal_url,
        "status": client.status,
        "submission_format": submission,
        "contacts": contacts,
        "created_at": client.created_at,
    }
