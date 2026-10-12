"""
Week 4 evidence — sample test messages.

15 short, support-ticket-style messages used to compare:
  (A) the open-ended approach  — ask the model to write a sentence, then parse it
  (B) the constrained approach — ask the model to return only a label + confidence

Mix of clearly urgent, clearly not urgent, and a few deliberately ambiguous ones,
so the comparison isn't testing only the easy cases.
"""

TEST_MESSAGES = [
    # Clearly urgent
    {"id": 1, "text": "Production is down, customers can't check out. Need this fixed NOW.", "true_label": "urgent"},
    {"id": 2, "text": "Payment gateway is throwing 500 errors for every transaction since 10am.", "true_label": "urgent"},
    {"id": 3, "text": "Our server room alarm is going off and I can't reach IT, please call me back immediately.", "true_label": "urgent"},
    {"id": 4, "text": "Data breach suspected — unauthorized logins detected in the admin panel.", "true_label": "urgent"},
    {"id": 5, "text": "Client's live demo starts in 20 minutes and the app is crashing on launch.", "true_label": "urgent"},

    # Clearly not urgent
    {"id": 6, "text": "Could you update the footer copyright year when you get a chance?", "true_label": "not urgent"},
    {"id": 7, "text": "Just curious — is there a dark mode planned for next quarter?", "true_label": "not urgent"},
    {"id": 8, "text": "Thanks for the demo yesterday, no action needed, just wanted to say it went well.", "true_label": "not urgent"},
    {"id": 9, "text": "Can we schedule a review of the Q3 roadmap sometime next month?", "true_label": "not urgent"},
    {"id": 10, "text": "Minor typo on the pricing page, 'recieve' should be 'receive'. No rush.", "true_label": "not urgent"},

    # Deliberately ambiguous
    {"id": 11, "text": "The export feature has been slow for a few days, getting a bit annoying.", "true_label": "ambiguous"},
    {"id": 12, "text": "A few users mentioned login is flaky sometimes. Might be worth a look soon.", "true_label": "ambiguous"},
    {"id": 13, "text": "Our biggest client emailed asking why their invoice looks wrong, waiting on us.", "true_label": "ambiguous"},
    {"id": 14, "text": "The weekly report didn't generate again, third time this month.", "true_label": "ambiguous"},
    {"id": 15, "text": "Noticed the staging environment is throwing warnings, not sure if it matters.", "true_label": "ambiguous"},
]
