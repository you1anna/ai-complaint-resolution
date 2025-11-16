"""
Seed database with dummy data for testing
Creates realistic policy documents and complaints
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
from src.models import PolicyDocument, Complaint, ComplaintStatus
from src.database import Database
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Sample policy documents
POLICIES = [
    {
        "policy_id": "EASY-IT-2024-001",
        "policy_name": "easyJet Travel Insurance - Italian Market",
        "language": "it",
        "version": "2024.1",
        "content": """
POLIZZA ASSICURATIVA DI VIAGGIO EASYJET

SEZIONE 1 - COPERTURA MEDICA
La presente polizza copre le spese mediche d'emergenza sostenute durante il viaggio fino a €50.000 per persona.

Cosa è coperto:
- Spese ospedaliere d'emergenza
- Trattamenti medici d'urgenza
- Prescrizioni mediche d'emergenza
- Trasporto d'emergenza in ambulanza

Esclusioni:
- Condizioni mediche preesistenti non dichiarate
- Trattamenti non d'emergenza o elettivi
- Infortuni derivanti da attività ad alto rischio (es. paracadutismo, alpinismo)
- Spese sostenute dopo il ritorno nel paese di residenza

SEZIONE 2 - CANCELLAZIONE VIAGGIO
Copre le spese di cancellazione fino a €5.000 per i seguenti motivi:

Motivi coperti:
- Malattia grave o infortunio dell'assicurato o di un familiare stretto
- Decesso di un familiare stretto
- Giuria obbligatoria o convocazione in tribunale come testimone
- Furto o danni gravi alla proprietà principale
- Licenziamento involontario (dopo 2 anni di impiego continuativo)

Esclusioni:
- Cambiamenti di programma volontari
- Disinclination a viaggiare o cambio d'idea
- Circostanze note al momento dell'acquisto della polizza
- Fallimento del tour operator (coperto da ATOL)

SEZIONE 3 - BAGAGLIO E EFFETTI PERSONALI
Copertura fino a €2.500 per bagaglio smarrito, rubato o danneggiato.

Limiti per articolo:
- Oggetti di valore singoli: max €300
- Apparecchiature elettroniche: max €500 totale
- Gioielli e orologi: max €200 totale

Esclusioni:
- Denaro contante, titoli e documenti
- Perdita dovuta a usura normale
- Bagaglio non custodito o lasciato incustodito
- Articoli in eccesso non dichiarati

SEZIONE 4 - RITARDO VIAGGIO
Compensazione per ritardi oltre le 12 ore: €50 per prime 12 ore, poi €25 per ogni 12 ore aggiuntive (max €200).

Requisiti:
- Conferma scritta dalla compagnia aerea del ritardo
- Ricevute per spese sostenute durante il ritardo

DEFINIZIONI IMPORTANTI:
- Familiare stretto: coniuge, partner, genitori, figli, fratelli, sorelle
- Condizione preesistente: qualsiasi condizione medica per cui si è ricevuto consulto, diagnosi o trattamento nei 12 mesi precedenti

PROCEDURA DI RECLAMO:
1. Contattare il centro assistenza entro 24 ore dall'incidente
2. Fornire tutta la documentazione di supporto entro 28 giorni
3. Conservare ricevute e prove di spesa originali
        """,
    },
    {
        "policy_id": "EASY-UK-2024-001",
        "policy_name": "easyJet Travel Insurance - UK Market",
        "language": "en",
        "version": "2024.1",
        "content": """
EASYJET TRAVEL INSURANCE POLICY

SECTION 1 - MEDICAL COVERAGE
This policy covers emergency medical expenses incurred during your trip up to £50,000 per person.

What's covered:
- Emergency hospital treatment
- Emergency medical treatment
- Emergency prescription medications
- Emergency ambulance transportation

Exclusions:
- Undeclared pre-existing medical conditions
- Non-emergency or elective treatment
- Injuries from high-risk activities (e.g., skydiving, mountaineering)
- Expenses incurred after returning to your country of residence

SECTION 2 - TRIP CANCELLATION
Covers cancellation costs up to £5,000 for the following reasons:

Covered reasons:
- Serious illness or injury of the insured or close family member
- Death of a close family member
- Compulsory jury service or court witness summons
- Theft of or serious damage to main residence
- Involuntary redundancy (after 2 years continuous employment)

Exclusions:
- Voluntary changes to plans
- Disinclination to travel or change of mind
- Circumstances known at time of policy purchase
- Tour operator insolvency (covered by ATOL)

SECTION 3 - BAGGAGE AND PERSONAL POSSESSIONS
Cover up to £2,500 for lost, stolen, or damaged baggage.

Single item limits:
- Individual valuables: max £300
- Electronic equipment: max £500 total
- Jewelry and watches: max £200 total

Exclusions:
- Cash, securities, and documents
- Loss due to normal wear and tear
- Unattended or unsupervised baggage
- Excess items not declared

SECTION 4 - TRAVEL DELAY
Compensation for delays over 12 hours: £50 for first 12 hours, then £25 for each additional 12 hours (max £200).

Requirements:
- Written confirmation from airline of delay
- Receipts for expenses incurred during delay

IMPORTANT DEFINITIONS:
- Close family member: spouse, partner, parents, children, siblings
- Pre-existing condition: any medical condition for which you received consultation, diagnosis, or treatment in the preceding 12 months

COMPLAINTS PROCEDURE:
1. Contact our assistance center within 24 hours of incident
2. Provide all supporting documentation within 28 days
3. Keep original receipts and proof of expenditure
        """,
    },
]

# Sample complaints
COMPLAINTS = [
    {
        "complaint_id": "COMP-2024-001",
        "customer_name": "Marco Rossi",
        "customer_language": "it",
        "policy_number": "EASY-IT-2024-001",
        "claim_reference": "CLM-IT-20241015-789",
        "complaint_text": """
Gentili Signori,

sono estremamente deluso dal modo in cui è stato gestito il mio reclamo.
Ho dovuto annullare il mio viaggio a Londra a causa di una grave emergenza medica -
mio padre è stato ricoverato in ospedale con un infarto il 10 ottobre.

Ho presentato tutti i documenti richiesti: certificato medico dell'ospedale,
prenotazione del volo cancellato, e la ricevuta della polizza assicurativa.
Nonostante questo, il mio reclamo è stato respinto con la motivazione che
"la condizione medica era preesistente".

Questo è assolutamente falso! Mio padre non ha mai avuto problemi cardiaci prima.
L'infarto è stato completamente inaspettato. Ho pagato €1.200 per i biglietti
aerei non rimborsabili e ritengo che questo rientri chiaramente nella copertura
per cancellazione del viaggio.

Richiedo una revisione immediata di questa decisione. Se non riceverò una risposta
soddisfacente, porterò questo caso all'IVASS.

Cordiali saluti,
Marco Rossi
        """,
        "days_until_deadline": 10,
    },
    {
        "complaint_id": "COMP-2024-002",
        "customer_name": "Sarah Williams",
        "customer_language": "en",
        "policy_number": "EASY-UK-2024-001",
        "claim_reference": "CLM-UK-20241018-456",
        "complaint_text": """
Dear Sir/Madam,

I am writing to complain about the handling of my baggage claim and the
unacceptable service I have received.

My luggage was stolen from the airport carousel in Rome on 15th October.
I reported it immediately to the police and your 24-hour helpline. The bag
contained my laptop (value £800), camera (value £400), and clothes/toiletries
worth approximately £300.

Your claims team has offered me only £500, stating that electronics are
limited to £500 total under the policy. However, this seems grossly unfair
given that I paid for comprehensive cover and the total value of my loss is £1,500.

Furthermore, your team took 3 weeks to respond to my initial claim, and I
have had to chase multiple times via phone and email. Each time I call,
I speak to a different person who seems unaware of my case.

I expect:
1. Full compensation of £1,500 for my stolen items
2. An explanation of why the claim took so long to process
3. An apology for the poor service

I have been a loyal easyJet customer for 5 years and am very disappointed.
If this is not resolved satisfactorily, I will escalate to the Financial Ombudsman.

Yours faithfully,
Sarah Williams
        """,
        "days_until_deadline": 12,
    },
    {
        "complaint_id": "COMP-2024-003",
        "customer_name": "Giovanni Bianchi",
        "customer_language": "it",
        "policy_number": "EASY-IT-2024-001",
        "claim_reference": "CLM-IT-20241020-123",
        "complaint_text": """
Buongiorno,

scrivo per lamentarmi del ritardo nel pagamento del mio indennizzo per ritardo del volo.

Il mio volo da Milano a Barcellona del 5 ottobre è stato ritardato di 18 ore
a causa di problemi tecnici dell'aereo. Ho fornito tutta la documentazione
richiesta inclusa la conferma scritta di easyJet del ritardo e le ricevute
per i pasti e l'hotel che ho dovuto pagare (totale €120).

Secondo la vostra polizza, dovrei ricevere £50 per le prime 12 ore più £25
per le 6 ore aggiuntive, quindi £75 in totale, più il rimborso delle spese sostenute.

Sono passate 4 settimane dalla presentazione del reclamo e non ho ancora
ricevuto alcun pagamento né comunicazione. Quando chiamo il vostro servizio clienti,
mi dicono solo che "il reclamo è in fase di elaborazione".

Questo è inaccettabile. Richiedo il pagamento immediato dell'indennizzo
dovuto più il rimborso delle mie spese vive.

Distinti saluti,
Giovanni Bianchi
        """,
        "days_until_deadline": 8,
    },
    {
        "complaint_id": "COMP-2024-004",
        "customer_name": "Emma Thompson",
        "customer_language": "en",
        "policy_number": "EASY-UK-2024-001",
        "claim_reference": None,
        "complaint_text": """
To Whom It May Concern,

I am writing to express my extreme dissatisfaction with your customer service
and to seek clarification on my policy coverage.

I attempted to make a claim for medical expenses incurred during my trip to
Spain in September. I suffered a severe allergic reaction and required emergency
hospital treatment. The hospital bill came to €2,300.

When I called your helpline, the representative told me that allergies are not
covered as they are considered "pre-existing conditions". This is ridiculous -
I have never had this allergy before! It was a completely unexpected reaction
to something I ate.

I have tried calling back multiple times to speak to a manager, but each time
I am told someone will call me back, and no one ever does. I have been left
out of pocket for over £2,000, and I am seriously considering legal action.

Your policy document is also very unclear about what constitutes a "pre-existing
condition". If I had known that a random allergic reaction wouldn't be covered,
I would never have purchased this policy.

I demand:
1. Immediate payment of my medical expenses
2. A clear explanation of your pre-existing conditions policy
3. Compensation for the stress and inconvenience caused

This is completely unacceptable and I will be contacting the Financial Ombudsman
Service if I don't receive a satisfactory response within 7 days.

Regards,
Emma Thompson
        """,
        "days_until_deadline": 5,
    },
    {
        "complaint_id": "COMP-2024-005",
        "customer_name": "Lucia Ferrari",
        "customer_language": "it",
        "policy_number": "EASY-IT-2024-001",
        "claim_reference": "CLM-IT-20241012-567",
        "complaint_text": """
Gentile Servizio Clienti,

vi contatto in merito al rifiuto del mio reclamo per cancellazione viaggio,
che trovo ingiusto e mal gestito.

Ho dovuto cancellare la mia vacanza a Parigi prevista per il 20 ottobre
perché sono stata licenziata dalla mia azienda il 15 settembre. Ho lavorato
per questa azienda per 3 anni e il licenziamento è stato completamente
inaspettato a causa di ristrutturazione aziendale.

La vostra polizza afferma chiaramente che copre il "licenziamento involontario
dopo 2 anni di impiego continuativo". Io soddisfo tutti questi requisiti.
Ho fornito la lettera di licenziamento, il contratto di lavoro che dimostra
i miei 3 anni di impiego, e tutti i documenti di viaggio.

Tuttavia, il vostro ufficio reclami ha respinto la mia richiesta dicendo che
"la ristrutturazione aziendale era di pubblico dominio". Questo è irrilevante!
Il punto è che IO non sapevo che sarei stata licenziata quando ho prenotato
la vacanza a luglio.

Questa decisione è estremamente ingiusta e mi ha causato significativo disagio
finanziario. Ho perso €850 in costi di viaggio non rimborsabili.

Chiedo una revisione urgente di questa decisione e un risarcimento completo.

Cordialmente,
Lucia Ferrari
        """,
        "days_until_deadline": 14,
    },
]


def seed_database():
    """Seed the database with dummy data"""
    logger.info("Starting database seeding...")

    db = Database()

    # Add policies
    logger.info("Adding policies...")
    for policy_data in POLICIES:
        policy = PolicyDocument(
            policy_id=policy_data["policy_id"],
            policy_name=policy_data["policy_name"],
            language=policy_data["language"],
            content=policy_data["content"],
            version=policy_data["version"],
            effective_date=datetime(2024, 1, 1)
        )
        db.save_policy(policy)
        logger.info(f"Added policy: {policy.policy_id}")

    # Add complaints
    logger.info("Adding complaints...")
    for complaint_data in COMPLAINTS:
        received_date = datetime.utcnow() - timedelta(days=7)  # Received 7 days ago
        deadline_date = received_date + timedelta(days=complaint_data["days_until_deadline"])

        complaint = Complaint(
            complaint_id=complaint_data["complaint_id"],
            customer_name=complaint_data["customer_name"],
            customer_language=complaint_data["customer_language"],
            policy_number=complaint_data["policy_number"],
            claim_reference=complaint_data["claim_reference"],
            complaint_text=complaint_data["complaint_text"],
            received_date=received_date,
            deadline_date=deadline_date,
            status=ComplaintStatus.NEW
        )
        db.save_complaint(complaint)
        logger.info(f"Added complaint: {complaint.complaint_id}")

    db.close()

    logger.info("Database seeding completed successfully!")
    logger.info(f"Added {len(POLICIES)} policies and {len(COMPLAINTS)} complaints")


if __name__ == "__main__":
    seed_database()
