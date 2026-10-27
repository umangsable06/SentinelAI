# scripts/ai_explanation.py — Phase 5: AI-Generated Alert Explanations
#
# PURPOSE:
#   For each high-risk alert (Medium, High, or Critical), call the Claude API
#   (Anthropic) to generate a plain-English explanation of:
#     - Why this network flow looks suspicious
#     - What type of attack it likely is
#     - What action a security analyst should take
#
#   The explanation is added as a new column "AI Explanation" in alerts.csv.
#
#   If no API key is set, a built-in rule-based fallback explanation is used
#   instead so the project still works without an API key.
#
# RUN: python scripts/ai_explanation.py

import sys
import os
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
from dotenv import load_dotenv

import config

# Load .env file so ANTHROPIC_API_KEY is available
load_dotenv(ROOT / ".env")


# ── Rule-based fallback explanations (used when no API key is set) ────────────

FALLBACK_EXPLANATIONS = {
    "DDoS": (
        "This flow shows characteristics consistent with a Distributed Denial of Service (DDoS) attack. "
        "The extremely high flow rate and packet volume suggest an attempt to overwhelm the target system "
        "with traffic, making it unavailable to legitimate users. "
        "Recommended action: Block the source IP at the firewall immediately and notify the network team."
    ),
    "PortScan": (
        "This flow exhibits port scanning behaviour. The pattern of many short connections to different "
        "destination ports is a classic reconnaissance technique — the attacker is probing the target "
        "to discover which services are running and potentially vulnerable. "
        "Recommended action: Block the source IP and review firewall rules to close unnecessary open ports."
    ),
    "BruteForce": (
        "This flow shows signs of a brute force attack. Repeated connection attempts to the same port "
        "(likely SSH on port 22 or FTP on port 21) suggest an automated tool is trying many "
        "username/password combinations to gain unauthorised access. "
        "Recommended action: Temporarily block the source IP, enable account lockout policies, "
        "and consider switching SSH to key-based authentication."
    ),
    "Other": (
        "This flow has been flagged as suspicious but does not match a specific known attack pattern. "
        "It may represent a web application attack, injection attempt, or other less common threat. "
        "Recommended action: Review the full packet capture if available and escalate to a senior analyst."
    ),
    "BENIGN": (
        "This flow was flagged due to unusual statistical characteristics, but the classifier "
        "predicts it is likely benign traffic. This may be a false positive caused by an unusual "
        "but legitimate application or a scheduled network task. "
        "Recommended action: Monitor for recurrence but no immediate action required."
    ),
}


def get_fallback_explanation(row: pd.Series) -> str:
    """Return a rule-based explanation when Claude API is not available."""
    label = row.get("Predicted Label", "BENIGN")
    base  = FALLBACK_EXPLANATIONS.get(label, FALLBACK_EXPLANATIONS["Other"])

    # Add specific numeric context from this row
    context = (
        f" [Risk Score: {row['Risk Score']}/10 | "
        f"Severity: {row['Severity']} | "
        f"Anomaly signal: {row['IF Score (0-10)']}/10 | "
        f"Attack confidence: {row['XGB Score (0-10)']}/10]"
    )
    return base + context


def build_claude_prompt(row: pd.Series) -> str:
    """
    Build the prompt we send to Claude for this specific alert.

    We give Claude:
    - The predicted attack type
    - The risk score and severity
    - The two model component scores
    - Source and destination IP

    We ask Claude to explain it in plain English for a junior security analyst.
    """
    return f"""You are a cybersecurity analyst assistant. A network intrusion detection system has flagged the following network flow as suspicious.

Alert Details:
- Source IP: {row['Source IP']}
- Destination IP: {row['Destination IP']}
- Predicted Attack Type: {row['Predicted Label']}
- Risk Score: {row['Risk Score']} out of 10
- Severity: {row['Severity']}
- Anomaly Detection Score: {row['IF Score (0-10)']} out of 10
- Attack Classifier Confidence: {row['XGB Score (0-10)']} out of 10

Write a brief, clear explanation (3-4 sentences) for a junior security analyst that:
1. Explains why this traffic looks suspicious based on the attack type and scores
2. Describes what the attacker is likely trying to do
3. Recommends one concrete action the analyst should take immediately

Keep the explanation practical and jargon-free where possible."""


def get_claude_explanation(client, row: pd.Series) -> str:
    """
    Call the Claude API to get an explanation for this alert.
    Returns the explanation text, or raises an exception if the call fails.
    """
    prompt = build_claude_prompt(row)

    message = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=config.CLAUDE_MAX_TOKENS,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return message.content[0].text.strip()


def main():
    print("=" * 60)
    print("SentinelAI — Phase 5: AI Explanation")
    print("=" * 60)

    # ── Load alerts from Phase 4 ──────────────────────────────────────────────
    alerts_path = Path(config.PROCESSED_DATA_DIR) / "alerts.csv"
    if not alerts_path.exists():
        raise FileNotFoundError(
            f"alerts.csv not found. Run Phase 4 first: python scripts/risk_scoring.py"
        )

    alerts = pd.read_csv(alerts_path)
    print(f"Loaded {len(alerts):,} alerts from Phase 4.")

    # ── Check for API key ─────────────────────────────────────────────────────
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    use_claude = bool(api_key and api_key != "your_anthropic_api_key_here")

    if use_claude:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        print(f"Anthropic API key found. Using Claude ({config.CLAUDE_MODEL}).")
    else:
        client = None
        print("No API key found in .env — using built-in rule-based explanations.")
        print("To use Claude: copy .env.example to .env and add your API key.")

    # ── Decide which alerts get explanations ──────────────────────────────────
    # Only generate explanations for Medium, High, and Critical alerts.
    # Low-severity alerts get a simple "no action required" note.
    # This avoids making hundreds of API calls for unimportant flows.
    explain_mask = alerts["Severity"].isin(["Medium", "High", "Critical"])
    explain_count = explain_mask.sum()
    skip_count    = (~explain_mask).sum()

    print(f"\nGenerating explanations for {explain_count:,} alerts "
          f"(Medium/High/Critical only).")
    print(f"Skipping {skip_count:,} Low-severity alerts.")

    # ── Generate explanations ─────────────────────────────────────────────────
    explanations = []
    success = 0
    fallback_used = 0

    for i, (idx, row) in enumerate(alerts.iterrows()):
        if not explain_mask.iloc[i]:
            # Low severity — short standard note
            explanations.append(
                f"Low risk flow. Predicted as {row['Predicted Label']} with risk score "
                f"{row['Risk Score']}/10. No immediate action required — logged for monitoring."
            )
            continue

        # Try Claude first; fall back to rule-based if API unavailable
        if use_claude:
            try:
                explanation = get_claude_explanation(client, row)
                success += 1
                # Small delay to respect API rate limits
                time.sleep(0.5)
            except Exception as e:
                print(f"  Warning: Claude API call failed for row {i}: {e}")
                explanation = get_fallback_explanation(row)
                fallback_used += 1
        else:
            explanation = get_fallback_explanation(row)
            fallback_used += 1

        explanations.append(explanation)

        # Progress indicator every 20 rows
        if (i + 1) % 20 == 0 or (i + 1) == len(alerts):
            print(f"  Processed {i + 1}/{len(alerts)} alerts...")

    # ── Add explanations to dataframe ─────────────────────────────────────────
    alerts["AI Explanation"] = explanations

    # ── Print sample outputs ──────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("SAMPLE EXPLANATIONS")
    print("=" * 60)

    # Show one example from each severity level
    for sev in ["Critical", "High", "Medium", "Low"]:
        sample = alerts[alerts["Severity"] == sev]
        if len(sample) > 0:
            row = sample.iloc[0]
            print(f"\n[{sev}] {row['Predicted Label']} — Risk: {row['Risk Score']}/10")
            print(f"Source: {row['Source IP']} -> {row['Destination IP']}")
            print(f"Explanation: {row['AI Explanation'][:300]}...")

    # ── Save updated alerts ───────────────────────────────────────────────────
    out_path = Path(config.PROCESSED_DATA_DIR) / "alerts_with_explanations.csv"
    alerts.to_csv(out_path, index=False)
    print(f"\nSaved: {out_path}")

    # Summary
    print(f"\nSummary:")
    if use_claude:
        print(f"  Claude explanations generated: {success:,}")
        print(f"  Fallback explanations used:    {fallback_used:,}")
    else:
        print(f"  Rule-based explanations used:  {fallback_used + skip_count:,}")

    print("\n" + "=" * 60)
    print("Phase 5 complete.")
    print("Run Phase 6 with: python src/database.py")
    print("=" * 60)

    return alerts


if __name__ == "__main__":
    main()
