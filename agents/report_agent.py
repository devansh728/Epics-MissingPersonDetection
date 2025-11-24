"""
PDF Report Generation Agent
Generates detailed PDF reports for CCTV scan results
"""

import os
import sys
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle,
    PageBreak,
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_db_connection


def generate_cctv_scan_report(case_id, cctv_id, scan_data, output_dir="reports"):
    """
    Generate PDF report for a single CCTV scan.

    Args:
        case_id: Case ID
        cctv_id: CCTV location ID
        scan_data: Scan results from surveillance.py
        output_dir: Output directory for reports

    Returns:
        Path to generated PDF report
    """
    try:
        os.makedirs(output_dir, exist_ok=True)

        # Get case and CCTV details from database
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM missing_cases WHERE id = ?", (case_id,))
        case_row = cursor.fetchone()
        if not case_row:
            print(f"[ERROR] Case {case_id} not found")
            return None
        case = dict(case_row)

        cursor.execute("SELECT * FROM cctv_locations WHERE id = ?", (cctv_id,))
        cctv_row = cursor.fetchone()
        if not cctv_row:
            print(f"[ERROR] CCTV {cctv_id} not found")
            return None
        cctv = dict(cctv_row)

        conn.close()

        # Create PDF filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"case{case_id}_cctv{cctv_id}_{timestamp}.pdf"
        filepath = os.path.join(output_dir, filename)

        # Create PDF document
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#1a237e"),
            spaceAfter=30,
            alignment=TA_CENTER,
        )

        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=16,
            textColor=colors.HexColor("#283593"),
            spaceAfter=12,
            spaceBefore=12,
        )

        # Title
        story.append(Paragraph("CCTV Scan Report", title_style))
        story.append(Spacer(1, 0.2 * inch))

        # Case Information
        story.append(Paragraph("Case Information", heading_style))
        case_data = [
            ["Case ID:", str(case["id"])],
            ["Name:", case["name"]],
            ["Age:", str(case["age"])],
            ["Last Seen:", case["last_seen_location"]],
            ["Date Reported:", case["date_reported"]],
            ["Emotion:", case["emotion"]],
        ]
        case_table = Table(case_data, colWidths=[2 * inch, 4 * inch])
        case_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e3f2fd")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                ]
            )
        )
        story.append(case_table)
        story.append(Spacer(1, 0.3 * inch))

        # CCTV Information
        story.append(Paragraph("CCTV Location", heading_style))
        cctv_data = [
            ["CCTV ID:", str(cctv["id"])],
            ["Name:", cctv["name"]],
            ["Type:", cctv["type"]],
            ["Location:", f"Lat: {cctv['lat']}, Lon: {cctv['lon']}"],
            ["Video Path:", cctv["video_path"]],
        ]
        cctv_table = Table(cctv_data, colWidths=[2 * inch, 4 * inch])
        cctv_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e8f5e9")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                ]
            )
        )
        story.append(cctv_table)
        story.append(Spacer(1, 0.3 * inch))

        # Scan Results
        story.append(Paragraph("Scan Results", heading_style))

        if scan_data.get("success"):
            matches_found = scan_data.get("matches_found", 0)
            total_frames = scan_data.get("total_frames", 0)

            result_style = ParagraphStyle(
                "ResultStyle",
                parent=styles["Normal"],
                fontSize=12,
                textColor=(
                    colors.HexColor("#2e7d32")
                    if matches_found > 0
                    else colors.HexColor("#c62828")
                ),
            )

            if matches_found > 0:
                story.append(
                    Paragraph(f"<b>✓ MATCHES FOUND: {matches_found}</b>", result_style)
                )
            else:
                story.append(Paragraph("<b>✗ NO MATCHES FOUND</b>", result_style))

            story.append(Spacer(1, 0.2 * inch))

            scan_summary = [
                ["Total Frames Processed:", str(total_frames)],
                ["Matches Found:", str(matches_found)],
                ["Scan Timestamp:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            ]
            summary_table = Table(scan_summary, colWidths=[2.5 * inch, 3.5 * inch])
            summary_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#fff3e0")),
                        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                    ]
                )
            )
            story.append(summary_table)
            story.append(Spacer(1, 0.3 * inch))

            # Match Details
            if matches_found > 0:
                story.append(Paragraph("Match Details", heading_style))

                matches = scan_data.get("matches", [])
                match_data = [["Frame", "Similarity", "Confidence", "Timestamp"]]

                for match in matches[:10]:  # Limit to first 10 matches
                    match_data.append(
                        [
                            str(match["frame"]),
                            f"{match['similarity']:.4f}",
                            f"{match['confidence']:.2f}",
                            match["timestamp"],
                        ]
                    )

                match_table = Table(
                    match_data,
                    colWidths=[1.5 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch],
                )
                match_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1976d2")),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, 0), 11),
                            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                            ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ]
                    )
                )
                story.append(match_table)

                # Add matched images if available
                story.append(Spacer(1, 0.3 * inch))
                story.append(Paragraph("Matched Frames", heading_style))

                for idx, match in enumerate(matches[:3]):  # Show first 3 images
                    img_path = match.get("image_path")
                    if img_path and os.path.exists(img_path):
                        try:
                            img = Image(img_path, width=4 * inch, height=3 * inch)
                            story.append(img)
                            story.append(
                                Paragraph(
                                    f"Frame {match['frame']} - Similarity: {match['similarity']:.4f}",
                                    styles["Normal"],
                                )
                            )
                            story.append(Spacer(1, 0.2 * inch))
                        except Exception as e:
                            print(f"[WARNING] Could not add image {img_path}: {e}")
        else:
            error_msg = scan_data.get("error", "Unknown error")
            story.append(
                Paragraph(f"<b>Scan Failed:</b> {error_msg}", styles["Normal"])
            )

        # Build PDF
        doc.build(story)

        print(f"[INFO] Generated CCTV scan report: {filepath}")
        return filepath

    except Exception as e:
        print(f"[ERROR] Failed to generate CCTV scan report: {e}")
        return None


def generate_aggregate_report(case_id, scan_task_id, output_dir="reports"):
    """
    Generate aggregate PDF report for all CCTV scans in a case.

    Args:
        case_id: Case ID
        scan_task_id: Scan task ID
        output_dir: Output directory for reports

    Returns:
        Path to generated PDF report
    """
    try:
        os.makedirs(output_dir, exist_ok=True)

        # Get case and scan results from database
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM missing_cases WHERE id = ?", (case_id,))
        case_row = cursor.fetchone()
        if not case_row:
            print(f"[ERROR] Case {case_id} not found")
            return None
        case = dict(case_row)

        cursor.execute("SELECT * FROM scan_tasks WHERE id = ?", (scan_task_id,))
        scan_task_row = cursor.fetchone()
        if not scan_task_row:
            print(f"[ERROR] Scan task {scan_task_id} not found")
            return None
        scan_task = dict(scan_task_row)

        cursor.execute(
            """
            SELECT csr.*, cl.name as cctv_name, cl.type as cctv_type
            FROM cctv_scan_results csr
            JOIN cctv_locations cl ON csr.cctv_id = cl.id
            WHERE csr.scan_task_id = ?
        """,
            (scan_task_id,),
        )
        scan_results = [dict(row) for row in cursor.fetchall()]

        conn.close()

        # Create PDF filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"case{case_id}_aggregate_{timestamp}.pdf"
        filepath = os.path.join(output_dir, filename)

        # Create PDF document
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=26,
            textColor=colors.HexColor("#0d47a1"),
            spaceAfter=30,
            alignment=TA_CENTER,
        )

        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=16,
            textColor=colors.HexColor("#1565c0"),
            spaceAfter=12,
            spaceBefore=12,
        )

        # Title
        story.append(
            Paragraph("Missing Person Case - Aggregate Scan Report", title_style)
        )
        story.append(Spacer(1, 0.2 * inch))

        # Case Information
        story.append(Paragraph("Case Information", heading_style))
        case_data = [
            ["Case ID:", str(case["id"])],
            ["Name:", case["name"]],
            ["Age:", str(case["age"])],
            ["Last Seen:", case["last_seen_location"]],
            ["Time Lost:", case.get("time_lost", "N/A")],
            ["Date Reported:", case["date_reported"]],
            ["Status:", case["status"]],
        ]
        case_table = Table(case_data, colWidths=[2 * inch, 4 * inch])
        case_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e1f5fe")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                ]
            )
        )
        story.append(case_table)
        story.append(Spacer(1, 0.3 * inch))

        # Scan Task Summary
        story.append(Paragraph("Scan Task Summary", heading_style))
        total_detections = sum(result["detections_found"] for result in scan_results)

        task_data = [
            ["Total CCTVs Scanned:", str(scan_task["scanned_cctvs"])],
            ["Total Detections:", str(total_detections)],
            ["Started At:", scan_task.get("started_at", "N/A")],
            ["Completed At:", scan_task.get("completed_at", "N/A")],
            ["Status:", scan_task["status"]],
        ]
        task_table = Table(task_data, colWidths=[2.5 * inch, 3.5 * inch])
        task_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f3e5f5")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                ]
            )
        )
        story.append(task_table)
        story.append(Spacer(1, 0.3 * inch))

        # Individual CCTV Results
        story.append(Paragraph("CCTV Scan Results", heading_style))

        results_data = [["CCTV Name", "Type", "Detections", "Duration (s)", "Status"]]

        for result in scan_results:
            results_data.append(
                [
                    result["cctv_name"],
                    result["cctv_type"],
                    str(result["detections_found"]),
                    (
                        f"{result['scan_duration_seconds']:.2f}"
                        if result["scan_duration_seconds"]
                        else "N/A"
                    ),
                    "✓ Complete" if result["detections_found"] >= 0 else "✗ Failed",
                ]
            )

        results_table = Table(
            results_data, colWidths=[2 * inch, 1 * inch, 1 * inch, 1 * inch, 1.5 * inch]
        )
        results_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#43a047")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 11),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        story.append(results_table)
        story.append(Spacer(1, 0.3 * inch))

        # Conclusion
        story.append(Paragraph("Conclusion", heading_style))
        if total_detections > 0:
            conclusion_text = f"<b>PERSON POTENTIALLY FOUND!</b> Total of {total_detections} detection(s) across {scan_task['scanned_cctvs']} CCTV location(s). Please review individual CCTV reports for detailed match information."
            conclusion_style = ParagraphStyle(
                "Conclusion",
                parent=styles["Normal"],
                fontSize=12,
                textColor=colors.HexColor("#2e7d32"),
            )
        else:
            conclusion_text = f"No matches found across {scan_task['scanned_cctvs']} CCTV location(s). Monitoring will continue."
            conclusion_style = ParagraphStyle(
                "Conclusion",
                parent=styles["Normal"],
                fontSize=12,
                textColor=colors.HexColor("#d32f2f"),
            )

        story.append(Paragraph(conclusion_text, conclusion_style))

        # Build PDF
        doc.build(story)

        print(f"[INFO] Generated aggregate scan report: {filepath}")
        return filepath

    except Exception as e:
        print(f"[ERROR] Failed to generate aggregate report: {e}")
        return None
