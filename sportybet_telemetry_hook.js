// ==UserScript==
// @name         SportyBet Real-Time Market Lock Telemetry Hook
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Detects the exact millisecond SportyBet locks match odds and dispatches telemetry to local Python monitor for Delta-L latency benchmarking.
// @author       SportsAudioTelemetry
// @match        https://www.sportybet.com/*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    console.log("%c[Telemetry Hook] SportyBet Zero-Latency Market Lock Monitor Loaded 🟢", "color: #00ff00; font-weight: bold; font-size: 14px;");

    const LOCAL_TELEMETRY_ENDPOINT = "http://127.0.0.1:8765/sporty_lock";
    let lastLockTimestamp = 0;
    const DEBOUNCE_MS = 2500; // Prevent spamming duplicate pings for the same event

    function dispatchLockEvent(source, detail) {
        const now = Date.now();
        if (now - lastLockTimestamp < DEBOUNCE_MS) {
            return;
        }
        lastLockTimestamp = now;

        const matchTitle = document.title || "SportyBet Match";
        const payload = {
            event: "SPORTYBET_MARKET_LOCK",
            source: source,
            detail: detail,
            client_timestamp_ms: now,
            iso_utc: new Date(now).toISOString(),
            url: window.location.href,
            match_title: matchTitle
        };

        console.log(`%c[LOCK DETECTED] ${detail} at ${new Date(now).toISOString()} | Sending to Python...`, "color: #ff3300; font-weight: bold; font-size: 13px;");

        fetch(LOCAL_TELEMETRY_ENDPOINT, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload),
            mode: "cors"
        }).then(res => {
            console.log("%c[Telemetry Synced] -> Python Monitor ΔL Engine received event.", "color: #00ccff;");
        }).catch(err => {
            // Monitor might be stopped
        });
    }

    // 1. DOM Mutation Observer: Detects when odds buttons turn gray, disabled, or locked
    const lockObserver = new MutationObserver(function(mutations) {
        for (let mutation of mutations) {
            if (mutation.type === "attributes" && mutation.attributeName === "class") {
                const target = mutation.target;
                const className = (target.className || "").toString();

                if (className.includes("locked") || 
                    className.includes("disabled") || 
                    className.includes("suspended") ||
                    className.includes("m-market-suspended") ||
                    className.includes("m-table-cell--disabled") ||
                    className.includes("is-locked")) {
                    
                    dispatchLockEvent("DOM_CLASS_MUTATION", `Market odds locked (class: ${className.slice(0, 30)})`);
                    break;
                }
            } else if (mutation.addedNodes.length > 0) {
                for (let node of mutation.addedNodes) {
                    if (node.nodeType === 1) {
                        const nodeClass = (node.className || "").toString();
                        if (nodeClass.includes("lock") || nodeClass.includes("suspended") || node.querySelector?.("[class*='lock'], [class*='suspended']")) {
                            dispatchLockEvent("DOM_NODE_ADDED", "Lock icon or suspended overlay rendered");
                            break;
                        }
                    }
                }
            }
        }
    });

    // Start observing DOM changes on the match container
    lockObserver.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ["class", "disabled", "aria-disabled"]
    });

    // 2. WebSocket Hook: Captures live push messages if SportyBet uses WebSockets for live odds
    const originalWebSocket = window.WebSocket;
    window.WebSocket = function(url, protocols) {
        const ws = new originalWebSocket(url, protocols);

        ws.addEventListener("message", function(event) {
            try {
                const dataStr = typeof event.data === "string" ? event.data : "";
                if (dataStr.includes('"status":2') || 
                    dataStr.includes('"status":"suspended"') || 
                    dataStr.includes('"isSuspended":true') ||
                    dataStr.includes('"locked":true')) {
                    dispatchLockEvent("WEBSOCKET_PUSH", "SportyBet WebSocket received market suspension payload");
                }
            } catch (e) {}
        });

        return ws;
    };
    window.WebSocket.prototype = originalWebSocket.prototype;

})();
