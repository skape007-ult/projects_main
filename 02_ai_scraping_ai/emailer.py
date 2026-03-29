import smtplib
import logging
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date
from config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD, EMAIL_RECIPIENT

logger = logging.getLogger(__name__)


def markdown_to_html(text: str) -> str:
    text = re.sub(r'^\*\*(.+?)\*\*$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'^\d+\.\s+(.+)', r'<li>\1</li>', text, flags=re.MULTILINE)
    text = re.sub(r'^\*\s+(.+)', r'<li>\1</li>', text, flags=re.MULTILINE)
    text = re.sub(r'\[(.+?)\]\((https?://[^\)]+)\)', r'<a href="\2">\1</a>', text)
    text = re.sub(r'(?<!["\'>])(https?://[^\s<>"]+)', r'<a href="\1">\1</a>', text)
    paragraphs = text.split('\n\n')
    html_paragraphs = []
    for p in paragraphs:
        p = p.strip()
        if p:
            if p.startswith('<h2>') or p.startswith('<li>'):
                html_paragraphs.append(p)
            else:
                html_paragraphs.append(f'<p>{p}</p>')
    return '\n'.join(html_paragraphs)


def build_stats_html(stats: dict) -> str:
    if not stats:
        return ""

    source_rows = ""
    for source, count in sorted(
            stats.get("sources_by_type", {}).items(),
            key=lambda x: x[1],
            reverse=True
    ):
        source_rows += f"""
        <tr>
            <td style="padding: 4px 12px 4px 0; color: #666; font-size: 12px;">
                {source}
            </td>
            <td style="padding: 4px 0; font-weight: 500; font-size: 12px;">
                {count} articles
            </td>
        </tr>
        """

    total = stats.get("total_sources_checked", 0)
    extracted = stats.get("successfully_extracted", 0)
    skipped = stats.get("skipped_already_seen", 0)
    failed = stats.get("failed_no_content", 0)
    used = stats.get("used_in_briefing", 0)
    rejected = stats.get("rejected_low_quality", 0)
    fetch_time = stats.get("fetch_time_seconds", 0)
    synthesis_time = stats.get("synthesis_time_seconds", 0)
    total_time = stats.get("total_time_seconds", 0)
    rag_new = stats.get("rag_new_embedded", 0)
    rag_total = stats.get("rag_total_vectors", 0)

    quality_row = f"""
            <tr>
                <td style="padding: 6px 0; color: #666; font-size: 12px;">
                    Rejected (low quality)
                </td>
                <td style="padding: 6px 0; color: #e67e22; font-size: 12px;">
                    {rejected}
                </td>
            </tr>
    """ if rejected > 0 else ""

    rag_section = f"""
        <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 12px 0;">
        <p style="margin: 0 0 12px 0; font-size: 12px; font-weight: 600;
                  color: #888; text-transform: uppercase; letter-spacing: 0.5px;">
            Knowledge Base (RAG)
        </p>
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 4px 0; color: #666; font-size: 12px;">
                    New articles embedded today
                </td>
                <td style="padding: 4px 0; font-size: 12px;
                           font-weight: 500; color: #185FA5;">
                    +{rag_new}
                </td>
            </tr>
            <tr>
                <td style="padding: 4px 0; color: #666; font-size: 12px;">
                    Total vectors in knowledge base
                </td>
                <td style="padding: 4px 0; font-size: 12px; font-weight: 500;">
                    {rag_total:,}
                </td>
            </tr>
        </table>
    """ if rag_total > 0 else ""

    return f"""
    <div style="margin-top: 40px; padding: 20px; background: #f8f9fa;
                border-radius: 8px; border: 1px solid #e9ecef;">

        <h3 style="margin: 0 0 16px 0; font-size: 13px; font-weight: 600;
                   text-transform: uppercase; letter-spacing: 0.5px; color: #888;">
            Pipeline Stats
        </h3>

        <table style="width: 100%; border-collapse: collapse; margin-bottom: 16px;">
            <tr>
                <td style="padding: 6px 0; color: #666; width: 60%; font-size: 12px;">
                    Sources checked
                </td>
                <td style="padding: 6px 0; font-weight: 500; font-size: 12px;">
                    {total}
                </td>
            </tr>
            <tr style="background: #f0f0f0;">
                <td style="padding: 6px 8px; color: #666; font-size: 12px;">
                    Successfully extracted
                </td>
                <td style="padding: 6px 8px; font-weight: 500;
                           color: #2d7a2d; font-size: 12px;">
                    ✓ {extracted}
                </td>
            </tr>
            <tr>
                <td style="padding: 6px 0; color: #666; font-size: 12px;">
                    Used in briefing
                </td>
                <td style="padding: 6px 0; font-weight: 500;
                           color: #185FA5; font-size: 12px;">
                    → {used}
                </td>
            </tr>
            <tr style="background: #f0f0f0;">
                <td style="padding: 6px 8px; color: #666; font-size: 12px;">
                    Already seen (skipped)
                </td>
                <td style="padding: 6px 8px; color: #888; font-size: 12px;">
                    {skipped}
                </td>
            </tr>
            <tr>
                <td style="padding: 6px 0; color: #666; font-size: 12px;">
                    Failed extraction
                </td>
                <td style="padding: 6px 0; color: #c0392b; font-size: 12px;">
                    {failed}
                </td>
            </tr>
            {quality_row}
        </table>

        <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 12px 0;">

        <p style="margin: 0 0 12px 0; font-size: 12px; font-weight: 600;
                  color: #888; text-transform: uppercase; letter-spacing: 0.5px;">
            Articles by source
        </p>
        <table style="width: 100%; border-collapse: collapse;">
            {source_rows}
        </table>

        <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 12px 0;">

        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 4px 0; color: #666; font-size: 12px;">
                    Fetch time
                </td>
                <td style="padding: 4px 0; font-size: 12px;">
                    {fetch_time}s
                </td>
            </tr>
            <tr>
                <td style="padding: 4px 0; color: #666; font-size: 12px;">
                    Synthesis time
                </td>
                <td style="padding: 4px 0; font-size: 12px;">
                    {synthesis_time}s
                </td>
            </tr>
            <tr>
                <td style="padding: 4px 0; color: #666; font-size: 12px;
                           font-weight: 600;">
                    Total runtime
                </td>
                <td style="padding: 4px 0; font-size: 12px; font-weight: 600;">
                    {total_time}s
                </td>
            </tr>
        </table>

        {rag_section}

    </div>
    """


def send_briefing(briefing_text: str, stats):
    gmail_user = GMAIL_ADDRESS
    gmail_app_password = GMAIL_APP_PASSWORD
    recipient = EMAIL_RECIPIENT

    if not gmail_user or not gmail_app_password:
        logger.error("Gmail credentials not set in .env — skipping email.")
        return

    html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 800px;
                     margin: auto; padding: 20px; color: #1a1a1a; line-height: 1.6;">

            <h1 style="color: #2c2c2c; border-bottom: 2px solid #4a90e2;
                       padding-bottom: 10px;">
                Daily AI Briefing — {date.today().strftime('%B %d, %Y')}
            </h1>

            {markdown_to_html(briefing_text)}

            {build_stats_html(stats)}

        </body>
        </html>
        """

    recipients = [gmail_user]
    if recipient:
        recipients.append(recipient)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Daily AI Briefing — {date.today().strftime('%B %d, %Y')}"
    msg["From"] = gmail_user
    msg["To"] = ", ".join(recipients)

    msg.attach(MIMEText(briefing_text, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(gmail_user, gmail_app_password)
            server.sendmail(gmail_user, recipients, msg.as_string())
        logger.info("Briefing sent to inbox.")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
