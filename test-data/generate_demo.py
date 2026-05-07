#!/usr/bin/env python3
"""
Generate synthetic judgment PDFs for pipeline testing.
Requires: reportlab
"""
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "judgments")
os.makedirs(OUTPUT_DIR, exist_ok=True)

styles = getSampleStyleSheet()
heading_style = ParagraphStyle(
    "JudgmentHeading",
    parent=styles["Heading1"],
    alignment=1,  # center
    fontSize=16,
    spaceAfter=20,
    textColor=colors.black,
)
body_style = ParagraphStyle(
    "JudgmentBody",
    parent=styles["BodyText"],
    fontSize=11,
    leading=16,
    alignment=4,  # justified
)
order_style = ParagraphStyle(
    "OrderStyle",
    parent=styles["Heading2"],
    fontSize=13,
    textColor=colors.darkblue,
    spaceAfter=12,
)


def build_judgment(filename: str, title: str, preamble: str, history: str, order: str):
    path = os.path.join(OUTPUT_DIR, filename)
    doc = SimpleDocTemplate(path, pagesize=A4,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    story = []

    story.append(Paragraph("IN THE HIGH COURT OF KARNATAKA AT BENGALURU", heading_style))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(title, heading_style))
    story.append(Spacer(1, 0.3 * inch))

    story.append(Paragraph("PREAMBLE", order_style))
    story.append(Paragraph(preamble, body_style))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("PROCEDURAL HISTORY", order_style))
    story.append(Paragraph(history, body_style))
    story.append(Spacer(1, 0.2 * inch))

    story.append(PageBreak())
    story.append(Paragraph("ORDER", order_style))
    story.append(Paragraph(order, body_style))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Sd/-<br/>Registrar<br/>High Court of Karnataka", body_style))

    doc.build(story)
    print(f"Created {path}")


def main():
    # --- Demo 1: Simple directive ---
    build_judgment(
        filename="demo_01_simple_directive.pdf",
        title="Writ Petition No. 1234 of 2024",
        preamble=(
            "Petitioner: M/s. Green Valley Developers<br/>"
            "Respondent: State of Karnataka, Revenue Department<br/>"
            "Date of Order: 15 January 2024"
        ),
        history=(
            "The petitioner filed this writ petition seeking a direction to the respondent "
            "to sanction the building plan submitted on 12 March 2023. The respondent had "
            "rejected the plan citing non-compliance with zoning regulations. After hearing "
            "both parties and perusing the records, the matter is ripe for decision."
        ),
        order=(
            "1. The writ petition is allowed in part.<br/><br/>"
            "2. The respondent shall comply with the directions issued herein within 30 days from the date of this order.<br/><br/>"
            "3. The petitioner shall deposit the requisite fees, if any, within 15 days.<br/><br/>"
            "4. No costs."
        ),
    )

    # --- Demo 2: Conditional directive ---
    build_judgment(
        filename="demo_02_conditional_directive.pdf",
        title="Civil Petition No. 5678 of 2024",
        preamble=(
            "Petitioner: Ramesh Kumar<br/>"
            "Respondent: Bangalore Development Authority<br/>"
            "Date of Order: 22 February 2024"
        ),
        history=(
            "The petitioner approached this Court aggrieved by the inaction of the respondent "
            "in processing the application for khata transfer. Despite repeated representations, "
            "no action was taken. The respondent has filed a statement of objections."
        ),
        order=(
            "1. The petition is disposed of with the following directions:<br/><br/>"
            "2. If the petitioner files the requisite documents and undertaking within 15 days from the date of this order, "
            "the respondent shall process the khata transfer application within 30 days thereafter.<br/><br/>"
            "3. In the event of failure by the petitioner, this order shall stand automatically vacated.<br/><br/>"
            "4. Liberty reserved to the petitioner to approach this Court afresh, if necessary."
        ),
    )

    # --- Demo 3: Multi-department directive with appeal ---
    build_judgment(
        filename="demo_03_multi_dept_appeal.pdf",
        title="Public Interest Litigation No. 9012 of 2024",
        preamble=(
            "Petitioner: Citizens Forum for Urban Governance<br/>"
            "Respondents: State of Karnataka (Home Department); Bangalore Metropolitan Transport Corporation; "
            "Commissioner of Police, Bengaluru City<br/>"
            "Date of Order: 10 March 2024"
        ),
        history=(
            "This Public Interest Litigation was filed highlighting the lack of pedestrian safety infrastructure "
            "near major bus terminals in Bengaluru. The Court heard the learned counsel for the petitioners and "
            "the respondents, and perused the status reports filed by the Transport Corporation and the Police Department."
        ),
        order=(
            "1. The PIL is allowed with the following directions:<br/><br/>"
            "2. The Bangalore Metropolitan Transport Corporation (Transport Department) shall install pedestrian crossings, "
            "foot-over bridges, and tactile paving at the identified terminals within 90 days.<br/><br/>"
            "3. The Commissioner of Police, Bengaluru City (Home Department) shall depute traffic constables during peak hours "
            "and ensure strict enforcement of zebra-crossing rules within 30 days.<br/><br/>"
            "4. The State Government (Urban Development Department) shall release the earmarked funds within 15 days.<br/><br/>"
            "5. The respondents are at liberty to prefer an appeal against this order within 60 days, should they deem fit.<br/><br/>"
            "6. List the matter after 90 days for compliance verification."
        ),
    )


if __name__ == "__main__":
    main()
