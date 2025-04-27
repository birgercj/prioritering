import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Funksjon: Kalkulere totalt betalte renter og måneder for ett lån
def calculate_loan_reduction(loan_amount, interest_rate, monthly_payment, extra_payment):
    months = 0
    total_interest = 0
    balance = loan_amount

    while balance > 0:
        interest = balance * (interest_rate / 12)
        total_interest += interest
        principal_payment = monthly_payment + extra_payment - interest
        if principal_payment <= 0:
            return None, None
        balance -= principal_payment
        months += 1

    return total_interest, months

# Funksjon: Prioriter lån etter metode
def prioritize_loans(loans, method='avalanche'):
    if method == 'avalanche':
        return loans.sort_values(by='Rente (%)', ascending=False).reset_index(drop=True)
    elif method == 'snowball':
        return loans.sort_values(by='Saldo (kr)', ascending=True).reset_index(drop=True)
    else:
        return loans

# Funksjon: Kalkulere samlet rentekostnad
def calculate_total_interest(loans, payment_per_month):
    total_interest = 0
    loans = loans.copy()
    while loans['Saldo (kr)'].sum() > 0:
        for index, row in loans.iterrows():
            saldo = row['Saldo (kr)']
            rente = row['Rente (%)'] / 100
            if saldo > 0:
                interest = saldo * (rente / 12)
                total_interest += interest
                payment = min(payment_per_month, saldo + interest)
                principal_payment = payment - interest
                if principal_payment <= 0:
                    return None
                saldo -= principal_payment
                loans.at[index, 'Saldo (kr)'] = max(0, saldo)
    return total_interest

# Funksjon: Simulere nedbetalingshistorikk
def simulate_loan_payoff(loans, payment_per_month):
    loans = loans.copy()
    balances = []
    total_balance = loans['Saldo (kr)'].sum()
    balance = total_balance
    history = [balance]
    months = 0
    while balance > 0 and months < 500:
        for index, row in loans.iterrows():
            saldo = row['Saldo (kr)']
            rente = row['Rente (%)'] / 100
            if saldo > 0:
                interest = saldo * (rente / 12)
                payment = min(payment_per_month, saldo + interest)
                principal_payment = payment - interest
                saldo -= principal_payment
                loans.at[index, 'Saldo (kr)'] = max(0, saldo)
        balance = loans['Saldo (kr)'].sum()
        history.append(balance)
        months += 1
    return history

# Hovedapp
st.title("Full Suite: Lånekalkulator og Låneprioritering")

tab1, tab2 = st.tabs(["Ekstra betaling på ett lån", "Prioritering av flere lån"])

# Tab 1: Ekstra betaling
with tab1:
    st.header("Ekstra betaling på lån")

    loan_amount = st.number_input("Nåværende lånesaldo (kr):", min_value=0.0, value=2_000_000.0, step=10000.0)
    interest_rate = st.number_input("Nominell årlig rente (%):", min_value=0.0, value=5.0, step=0.1) / 100
    monthly_payment = st.number_input("Nåværende månedlig betaling (kr):", min_value=0.0, value=10000.0, step=100.0)
    extra_payment = st.number_input("Ekstra månedlig betaling (kr):", min_value=0.0, value=1000.0, step=100.0)

    if st.button("Beregn effekt av ekstra betaling", key="extra_payment"):
        original_interest, original_months = calculate_loan_reduction(loan_amount, interest_rate, monthly_payment, 0)
        new_interest, new_months = calculate_loan_reduction(loan_amount, interest_rate, monthly_payment, extra_payment)

        if original_interest is not None and new_interest is not None:
            saved_interest = original_interest - new_interest
            months_saved = original_months - new_months

            st.subheader("Resultat:")
            st.write(f"**Du sparer {saved_interest:,.0f} kr i renter.**")
            st.write(f"**Du betaler ned lånet {months_saved} måneder raskere.**")
        else:
            st.error("Betalingen dekker ikke rentene. Øk terminbeløpet eller ekstra innbetaling.")

# Tab 2: Prioritering av flere lån
with tab2:
    st.header("Prioritering av flere lån (opptil 5)")

    loans = []
    for i in range(1, 6):
        st.subheader(f"Lån {i}")
        saldo = st.number_input(f"Saldo for Lån {i} (kr):", min_value=0.0, step=1000.0, key=f"saldo_{i}")
        rente = st.number_input(f"Rente for Lån {i} (%):", min_value=0.0, step=0.1, key=f"rente_{i}")
        if saldo > 0:
            loans.append({"Lån": f"Lån {i}", "Saldo (kr)": saldo, "Rente (%)": rente})

    if loans:
        df_loans = pd.DataFrame(loans)

        st.subheader("Dine lån:")
        st.dataframe(df_loans)

        st.subheader("Innstilling: Total månedlig betaling")
        payment_per_month = st.number_input("Hvor mye vil du betale totalt på lånene hver måned? (kr)", 
                                            min_value=1000.0, value=5000.0, step=500.0)

        # Prioriter
        avalanche = prioritize_loans(df_loans, method='avalanche')
        snowball = prioritize_loans(df_loans, method='snowball')

        st.subheader("Avalanche (høyest rente først):")
        st.dataframe(avalanche)

        st.subheader("Snowball (lavest saldo først):")
        st.dataframe(snowball)

        # Beregning av renter
        avalanche_interest = calculate_total_interest(avalanche.copy(), payment_per_month)
        snowball_interest = calculate_total_interest(snowball.copy(), payment_per_month)

        if avalanche_interest is not None and snowball_interest is not None:
            st.subheader("Rentekostnad sammenligning:")
            st.write(f"**Total renter med Avalanche:** {avalanche_interest:,.0f} kr")
            st.write(f"**Total renter med Snowball:** {snowball_interest:,.0f} kr")

            interest_saved = snowball_interest - avalanche_interest
            if interest_saved > 0:
                st.success(f"**Ved å bruke Avalanche sparer du omtrent {interest_saved:,.0f} kr i renter!**")
            else:
                st.info("Ingen stor forskjell på valgt metode i dette tilfellet.")

        # Simulering for graf
        avalanche_sim = simulate_loan_payoff(avalanche.copy(), payment_per_month)
        snowball_sim = simulate_loan_payoff(snowball.copy(), payment_per_month)

        st.subheader("Graf: Nedbetaling over tid")

        plt.figure(figsize=(10, 5))
        plt.plot(avalanche_sim, label="Avalanche (høyeste rente først)")
        plt.plot(snowball_sim, label="Snowball (lavest saldo først)")
        plt.xlabel("Måneder")
        plt.ylabel("Gjeld (kr)")
        plt.title("Nedbetaling av gjeld over tid")
        plt.legend()
        plt.grid(True)
        st.pyplot(plt)

    else:
        st.info("Legg inn minst ett lån for å få prioriteringsliste og graf.")
