
(function() {
    'use strict';

    // ================== CONFIG ==================
    const BETSAVE_URL = 'https://api.betsave.io/postback'; // Production backend
    const PARTNER_ID = 'Stake'; // your BetSave partner ID
    const CLICKID = 'abc987'; // RedTrack campaign ID (adjust if dynamic)
    // ============================================

    function getData() {
        const data = [];
        const cards = document.querySelectorAll('div[data-testid$="-referred-user"]');

        cards.forEach(card => {
            try {
                const user_id = card.querySelector('span.ds-body-md')?.innerText.trim() || '';
                const partner = 'Stake';

                const container = card.closest('div.flex.flex-col.gap-3');

                // Total Wagered
                const total_wagered_text = container
                    .querySelector('div.flex.flex-1.flex-col.gap-6 span.ds-body-md-strong')
                    ?.innerText.replace("$", "").replace(",", "").trim() || '0';
                const total_wagered = parseFloat(total_wagered_text) || 0;

                // Total Deposits
                const depositLabel = Array.from(container.querySelectorAll('span.ds-body-md'))
                    .find(s => s.innerText.includes("Total Deposits"));
                const total_deposits = depositLabel
                    ? depositLabel.parentElement.nextElementSibling?.innerText.trim() || ''
                    : '';

                // Date (Registered / Last Deposit)
                const dateLabel = Array.from(container.querySelectorAll('span.ds-body-md'))
                    .find(s => s.innerText.includes("Registered") || s.innerText.includes("Last Deposit Date"));
                const date = dateLabel
                    ? dateLabel.parentElement.nextElementSibling?.innerText.trim() || ''
                    : '';

                if (user_id)
                    data.push({ user_id, partner, total_wagered, total_deposits, date });
            } catch (e) {
                console.log("Row parsing error:", e);
            }
        });

        return data;
    }

    async function sendToBetSave(user) {
        // Registration postback
        const regUrl = `${BETSAVE_URL}/registration?subid=${encodeURIComponent(user.user_id)}&partner_id=${PARTNER_ID}&clickid=${CLICKID}`;
        // Wager postback
        const wagerUrl = `${BETSAVE_URL}/wager?subid=${encodeURIComponent(user.user_id)}&partner_id=${PARTNER_ID}&amount=${user.total_wagered}&clickid=${CLICKID}`;

        try {
            const regRes = await fetch(regUrl);
            const regText = await regRes.text();
            console.log(`✅ [Registration] ${user.user_id}: ${regRes.status} | ${regText}`);
        } catch (err) {
            console.error(`❌ [Registration] ${user.user_id} failed:`, err);
        }

        try {
            const wagerRes = await fetch(wagerUrl);
            const wagerText = await wagerRes.text();
            console.log(`💰 [Wager] ${user.user_id}: ${wagerRes.status} | ${wagerText}`);
        } catch (err) {
            console.error(`❌ [Wager] ${user.user_id} failed:`, err);
        }
    }

    function downloadCSV(allData) {
        if (allData.length === 0) {
            alert("No referral data found. Make sure the page is fully loaded.");
            return;
        }

        const header = `"user_id","partner","total_wagered","total_deposits","date"`;
        const rows = allData.map(d =>
            `"${d.user_id}","${d.partner}",${d.total_wagered.toFixed(2)},"${d.total_deposits}","${d.date}"`
        );
        const csv = [header, ...rows].join("\n");

        const blob = new Blob([csv], { type: 'text/csv' });
        const a = document.createElement('a');
        const url = URL.createObjectURL(blob);
        a.href = url;
        a.download = `referrals_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        URL.revokeObjectURL(url);
    }

    const btn = document.createElement('button');
    btn.innerText = "📤 Sync with BetSave";
    Object.assign(btn.style, {
        position: "fixed",
        top: "10px",
        right: "10px",
        zIndex: 1000,
        padding: "10px 16px",
        backgroundColor: "#28a745",
        color: "white",
        border: "none",
        borderRadius: "6px",
        cursor: "pointer",
        fontWeight: "bold",
        fontSize: "14px"
    });

    btn.onclick = async () => {
        setTimeout(async () => {
            const data = getData();
            if (!data.length) {
                alert("No referral data found. Please make sure the page is fully loaded.");
                return;
            }

            console.log(`🚀 Starting BetSave sync for ${data.length} users...`);
            let successCount = 0;

            for (const user of data) {
                await sendToBetSave(user);
                successCount++;
            }

            downloadCSV(data);
            alert(`✅ Sync completed! ${successCount} users sent to BetSave.\nCSV file saved.`);
        }, 2000);
    };

    document.body.appendChild(btn);
})();
