import os
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv
load_dotenv('secrets.env')

# ==============================
# Configuration
# ==============================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

EMAIL_USER = os.getenv("EMAIL_USER", "example@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "xxxxxxxxxxxx")
TO_EMAIL = os.getenv("TO_EMAIL", "recipient@example.com")

URL = "https://www.stwdo.de/en/living-houses-application/current-housing-offers"

HEADERS = {
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    )
}


# ==============================
# Utility functions
# ==============================
def get_timestamp() -> str:
    """Return the current timestamp in a readable format."""
    return datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")


def fetch_housing_page(url: str) -> BeautifulSoup:
    """Fetch the housing offers page and return a BeautifulSoup parser."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch page: {e}")
    return BeautifulSoup(response.content, "html.parser")


def extract_options(soup: BeautifulSoup, field_name: str) -> list[str]:
    """
    Extract available (non-disabled) options from a <select> element.

    Args:
        soup: BeautifulSoup object of the page.
        field_name: The name attribute of the <select> element.

    Returns:
        A list of option strings, excluding the "All" placeholder.
    """
    selector = f'select[name="{field_name}"] > option:not([disabled])'
    options = [opt.text.strip() for opt in soup.select(selector)]
    return [opt for opt in options if opt and opt != "All"]


def build_html_table(cities: list[str], complexes: list[str]) -> str:
    """Generate an HTML table comparing available cities and complexes."""
    html = [
        '<table border="1" cellspacing="0" cellpadding="5" style="border-collapse: collapse;">',
        "<thead><tr><th>Cities</th><th>Residential Areas</th></tr></thead>",
        "<tbody>",
    ]

    max_len = max(len(cities), len(complexes))
    for i in range(max_len):
        city = cities[i] if i < len(cities) else ""
        area = complexes[i] if i < len(complexes) else ""
        html.append(f"<tr><td>{city}</td><td>{area}</td></tr>")

    html.append("</tbody></table>")
    return "\n".join(html)


def send_email_alert(html_table: str) -> None:
    """Send an email notification with the housing availability data."""
    subject = "🚨 STWDO Housing Availability Changed!"
    body = f"""
    <html>
      <body>
        <p>Changes detected in STWDO housing availability:</p>
        <p>
          Link: <a href="{URL}">STWDO Housing Offers</a>
        </p>
        {html_table}
      </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["From"] = EMAIL_USER
    msg["To"] = TO_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_USER, TO_EMAIL, msg.as_string())
        print(f"{get_timestamp()} Email alert sent!")
    except Exception as e:
        print(f"{get_timestamp()} Failed to send email: {e}")


# ==============================
# Main execution
# ==============================
def main():
    soup = fetch_housing_page(URL)

    cities = extract_options(
        soup, "tx_openimmo_list[tx_openimmo_list][city]"
    )
    complexes = extract_options(
        soup, "tx_openimmo_list[tx_openimmo_list][residentialComplex]"
    )

    if cities or complexes:
        html_table = build_html_table(cities, complexes)
        send_email_alert(html_table)
    else:
        print(f"{get_timestamp()} No housing availability detected.")


if __name__ == "__main__":
    main()
