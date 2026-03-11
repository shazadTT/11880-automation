import os
import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


def get_data():
    return {
        "firma":           os.environ.get("FIRMA", ""),
        "strasse":         os.environ.get("STRASSE", ""),
        "hausnummer":      os.environ.get("HAUSNUMMER", ""),
        "plz":             os.environ.get("PLZ", ""),
        "ort":             os.environ.get("ORT", ""),
        "telpre":          os.environ.get("TELPRE", ""),
        "telnummer":       os.environ.get("TELNUMMER", ""),
        "branche":         os.environ.get("BRANCHE", ""),
        "email":           os.environ.get("EMAIL", ""),
        "website":         os.environ.get("WEBSITE", ""),
        "kontakt_vorname": os.environ.get("KONTAKT_VORNAME", ""),
        "kontakt_nachname":os.environ.get("KONTAKT_NACHNAME", ""),
        "kontakt_email":   os.environ.get("KONTAKT_EMAIL", ""),
    }


def validiere(c):
    pflicht = ["firma", "strasse", "plz", "ort", "telpre",
               "telnummer", "branche", "kontakt_vorname",
               "kontakt_nachname", "kontakt_email"]
    fehlend = [f for f in pflicht if not c.get(f)]
    if fehlend:
        raise ValueError(f"Pflichtfelder fehlen: {', '.join(fehlend)}")


def cmp_entfernen(page):
    page.evaluate("""
        () => {
            document.querySelectorAll(
                '#cmpwrapper, .cmpwrapper, [id*="cmp"], [class*="cmpbox"], .cmp-container'
            ).forEach(el => el.remove());
            document.body.style.overflow = 'auto';
        }
    """)
    time.sleep(0.3)


def tippe(page, selector, wert):
    locator = page.locator(selector)
    locator.click()
    time.sleep(0.2)
    locator.fill("")
    page.keyboard.type(wert, delay=60)
    page.keyboard.press("Tab")
    time.sleep(0.3)


def fill_form(page, c):
    print(f"\nStarte Eintrag fuer: {c['firma']}")

    page.goto("https://firma-eintragen-kostenlos.11880.com/new/portal_header")
    page.wait_for_load_state("networkidle")
    time.sleep(3)

    # Cookie-Banner schliessen
    try:
        page.wait_for_selector("button:has-text('Ablehnen')", timeout=6000)
        page.click("button:has-text('Ablehnen')")
        time.sleep(1.5)
        print("  OK Cookie-Banner abgelehnt")
    except PlaywrightTimeout:
        print("  - Kein Cookie-Banner")
    cmp_entfernen(page)

    # Firmenname
    page.wait_for_selector("#company", timeout=15000)
    tippe(page, "#company", c["firma"])
    print("  OK Firmenname")

    # Branche - Autocomplete
    page.locator("#tradename").click()
    time.sleep(0.2)
    page.locator("#tradename").fill("")
    page.keyboard.type(c["branche"], delay=80)
    time.sleep(2)
    try:
        page.wait_for_selector(".sb-auto-suggest li, .suggest-entity li", timeout=4000)
        page.locator(".sb-auto-suggest li, .suggest-entity li").first.click()
        print("  OK Branche aus Dropdown")
    except PlaywrightTimeout:
        page.locator("#tradename").press("Tab")
        print("  - Branche per Tab")
    time.sleep(0.5)

    # Adresse
    tippe(page, "#streetname", c["strasse"])
    tippe(page, "#streetnr", c["hausnummer"])

    # PLZ mit Dropdown
    page.locator("#zipcode").click()
    time.sleep(0.2)
    page.locator("#zipcode").fill("")
    page.keyboard.type(c["plz"], delay=80)
    time.sleep(1.5)
    try:
        page.wait_for_selector(".sb-auto-suggest li, .suggest-location li", timeout=3000)
        page.locator(".sb-auto-suggest li, .suggest-location li").first.click()
        print("  OK PLZ aus Dropdown")
        time.sleep(0.5)
    except PlaywrightTimeout:
        page.locator("#zipcode").press("Tab")

    # Ort
    page.locator("#cityname").click()
    time.sleep(0.2)
    page.locator("#cityname").fill("")
    page.keyboard.type(c["ort"], delay=80)
    time.sleep(1.5)
    try:
        page.wait_for_selector(".sb-auto-suggest li, .suggest-location li", timeout=3000)
        page.locator(".sb-auto-suggest li, .suggest-location li").first.click()
        print("  OK Ort aus Dropdown")
        time.sleep(0.5)
    except PlaywrightTimeout:
        page.locator("#cityname").press("Tab")
        print("  - Ort per Tab")

    # Telefon
    tippe(page, "#phone_areacode", c["telpre"])
    tippe(page, "#phone_extension", c["telnummer"])
    print("  OK Telefon")

    # Optional
    if c["email"]:
        tippe(page, "#companyemail", c["email"])
    if c["website"]:
        tippe(page, "#homepage", c["website"])

    # Submit Schritt 1
    cmp_entfernen(page)
    page.locator(".js-response-edit-form__next-button").scroll_into_view_if_needed()
    time.sleep(0.5)
    page.locator(".js-response-edit-form__next-button").click()
    time.sleep(4)
    print("  OK Schritt 1 abgeschlossen")

    # Schritt 2: Kontaktdaten (Ansprechpartner)
    page.wait_for_load_state("networkidle")
    time.sleep(1)
    cmp_entfernen(page)
    aktuell = page.evaluate("() => document.title")
    print(f"  DEBUG Seite nach Schritt 1: {aktuell}")

    # Kontakt-Felder suchen und befuellen
    try:
        page.wait_for_selector("input[name*='firstname'], input[name*='vorname'], input[id*='firstname']", timeout=10000)
        vorname_sel = "input[name*='firstname'], input[name*='vorname'], input[id*='firstname']"
        page.locator(vorname_sel).first.fill(c["kontakt_vorname"])
        time.sleep(0.3)
        nachname_sel = "input[name*='lastname'], input[name*='nachname'], input[id*='lastname']"
        page.locator(nachname_sel).first.fill(c["kontakt_nachname"])
        time.sleep(0.3)
        email_sel = "input[name*='email'], input[id*='email']"
        page.locator(email_sel).first.fill(c["kontakt_email"])
        time.sleep(0.3)
        print("  OK Kontaktdaten")
    except PlaywrightTimeout:
        # Kein Kontaktformular - direkt weiter
        print("  - Kein Kontaktformular gefunden")

    # Finaler Submit
    cmp_entfernen(page)
    try:
        page.locator(".js-response-edit-form__next-button").scroll_into_view_if_needed()
        time.sleep(0.3)
        page.locator(".js-response-edit-form__next-button").click()
        time.sleep(4)
    except PlaywrightTimeout:
        page.evaluate("document.querySelector('.js-response-edit-form__next-button').click()")
        time.sleep(4)

    print("  OK Eintrag abgesendet!")
    print(f"\n  Bestaetigung geht an: {c['kontakt_email']}")


def main():
    print("=" * 55)
    print("11880.com Automatisierung")
    print("=" * 55)

    c = get_data()

    try:
        validiere(c)
    except ValueError as e:
        print(f"\nFehler: {e}")
        exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="de-DE"
        )
        page = context.new_page()

        try:
            fill_form(page, c)
            print("\nErfolgreich abgeschlossen!")
        except Exception as e:
            page.screenshot(path="fehler_screenshot.png")
            print(f"\nFehler: {e}")
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    main()
