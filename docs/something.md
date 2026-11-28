Here is a zero-to-hero crash course on everything in this repository (terf_deliverable). It is written in simple, plain English with intuitive
  analogies so you can confidently explain the project, defend it against your teacher's questions, and even demonstrate it live.
  ──────
   Part 1: The 60-Second "Elevator Pitch"
  │ "Teacher, in real-world IoT and Wireless Sensor Networks (like wildfire sensors in a forest or crop sensors in agriculture), small battery-powered
  │ devices pass messages to each other until they reach a central base station.
  │
  │ Traditional cybersecurity uses passwords and encryption, but that fails when a sensor is physically captured or hacked—because the hacked sensor
  │ already holds valid cryptographic keys (an Insider Threat).
  │
  │ Our project, TERF (Trust-Enhanced Random Forest), is an intelligent security system. Instead of relying on encryption, it monitors how nodes behave.
  │ We invented mathematical Trust Scores (measuring packet forwarding reliability and battery usage) and fed them into a Machine Learning algorithm
  │ (Random Forest). This allows us to catch stealthy insider attacks—specifically Grayhole attacks, where malicious nodes secretly drop packets while
  │ pretending it was just bad Wi-Fi—slashing missed attacks by 74%."
  ──────
   Part 2: Machine Learning 101 (The Core Concepts)

  You don't need a math degree to understand Machine Learning (ML). Here are the 5 terms you need to know:

   ML Term              │ Plain English Definition                                      │ In This Project
  ──────────────────────┼───────────────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────────
   Traditional Coding   │ A human writes rigid if/else rules: if packets_dropped > 50:  │ Hard to write rules for stealthy attacks that adapt or mimic
                        │ alert()                                                       │ bad signals.
   Machine Learning     │ You feed the computer thousands of past examples, and the     │ We showed the ML model 64,000 past sensor communication logs
                        │ algorithm learns the patterns itself.                         │ so it learned what normal vs. attack traffic looks like.
   Features (Inputs)    │ The clues/measurements the algorithm inspects.                │ Packet counts (DATA_S, DATA_F, DATA_D), battery energy
                        │                                                               │ (Energy), and our 4 custom Trust Scores.
   Labels (Targets)     │ The answer the algorithm tries to predict.                    │ 5 categories: Normal, Blackhole, Grayhole, Flooding,
                        │                                                               │ Scheduling.
   Training vs. Testing │ Like studying for an exam: you study practice questions with  │ We trained on 64,000 records and tested on 16,000 unseen
                        │ answers (Training Set: 80%), then take a test with brand new  │ records to prove it didn't just memorize the data.
                        │ unseen questions (Test Set: 20%).                             │

### What is a "Decision Tree"?

  Think of a game of 20 Questions or a medical flowchart:

  • "Did this node forward less than 60% of received data?" → Yes.
  • "Did its battery drain faster than normal?" → Yes → Prediction: Malicious Attack.

### What is a "Random Forest"?

  A single Decision Tree can make mistakes. A Random Forest creates a council of 60 different Decision Trees, each looking at random slices of the data.
  When a new sensor packet arrives, all 60 trees vote. The majority vote wins. This makes it extremely reliable and resistant to errors.
  ──────
   Part 3: The 4 Cyberattacks Explained Simply

  Our project detects normal operations plus 4 specific network attacks from the standard WSN-DS benchmark https://doi.org/10.1155/2016/4731953:

  ┌───────────────────────┐
  │                                   │
  │            WSN Traffic            ├───────────┐
    flowchart TD
        A["WSN Traffic"] --> B["Normal Traffic (Safe)"]
        A --> C["The 4 Attacks"]
        C --> C1["1. Blackhole (Greedy Traitor)Drops 100% of packets"]
        C --> C2["2. Grayhole (Sneaky Traitor)Drops 30%-60% of packets (Hardest to catch!)"]
        C --> C3["3. Flooding (Spammer)Spams broadcast messages to drain batteries"]
        C --> C4["4. Scheduling (Rude Interrupter)Transmits out of its assigned time-slot"]

1. Blackhole Attack (100% Drop):
   • Analogy: A rogue mailman who takes all incoming letters and throws 100% of them in an incinerator.
   • Difficulty: Very easy to catch because 0 letters arrive (DATA_F = 0).
2. Grayhole / Selective Forwarding Attack (The Sneaky Attack):
   • Analogy: A mailman who delivers half your mail, but secretly shreds critical bank statements. When caught, he claims "the wind blew them away".
   • Difficulty: This is the hardest attack to detect. In wireless networks, normal radios drop 10%–20% of packets due to physical interference or
   walls. Grayhole attackers intentionally drop 30%–50% to hide inside normal wireless noise!
3. Flooding Attack (Denial of Sleep):
   • Analogy: Someone calling your phone 500 times a night so you can't sleep and your battery dies.
   • Difficulty: The attacker sends hundreds of fake connection requests, keeping sensor radios awake until their batteries run out.
4. Scheduling Attack (TDMA Collision):
   • Analogy: In a meeting where everyone is given 2 minutes to speak, one person talks out of turn, interrupting everyone else and causing chaos.

  ──────
   Part 4: The Core Innovation — What Makes "TERF" Special?

  If a teacher asks: "Why did you create TERF instead of just using standard Random Forest?"

### The Problem With Standard Machine Learning

  Standard Random Forest only looks at raw numbers (e.g., Dropped Packets = 35). It cannot tell whether 35 dropped packets was caused by a tree blocking
  the Wi-Fi signal or a sneaky Grayhole attacker. Because of this ambiguity, standard models misclassified 31 Grayhole attacks as safe Normal traffic.

### Our Solution: Feature Engineering with "Trust Scores"

  Before passing data to the Random Forest, our pipeline calculates 4 behavioral Trust Scores:

1. Direct Forwarding Trust:
   Packets Forwarded
   Direct Trust = ─────────────────
   Packets Received

  (Normal nodes score ≈ 0.93; Grayhole drops to ≈ 0.55; Blackhole drops to ≈ 0.04).
  2. Energy Trust: Current remaining battery divided by starting battery.
  3. Control Quota Trust: Measures whether a node is sending legitimate data or spamming control broadcasts (collapses during Flooding attacks).
  4. Composite Multi-Factor Trust: A unified health score:
    Composite Trust = 50% × Direct + 30% × Control + 20% × Energy

### The Empirical Proof:

  When we fed these Trust scores into Random Forest (TERF):
  • Missed Grayhole attacks dropped from 31 down to just 8 (a 74.2% reduction in false negatives).
  • Grayhole Recall jumped from 97.58% to 99.38%.
  • Algorithmic analysis showed Direct_Trust and Composite_Trust became the #1 and #2 most important features used by the model across all trees.
  ──────
   Part 5: How the Codebase is Organized

  Here is the structure of the repository:

   Folder / File                            │ What It Does
  ──────────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────
   pipeline/01_simulate_wsn_traffic.py      │ Data Generator: Simulates 100 sensor nodes operating under the LEACH protocol, injects the 4
                                            │ cyberattacks, calculates trust scores, and outputs 80,000 data rows into
                                            │ results/wsn_attack_simulation.csv.
   pipeline/02_train_and_evaluate_terf.py   │ The AI Brain: Trains 4 competing models (Logistic Regression, Decision Tree, Standard RF, and TERF) on
                                            │ 80% of data, tests them on the remaining 20%, and saves performance reports.
   frontend/server.py & frontend/index.html │ Interactive Demo: A web dashboard that runs on http://localhost:8000. You can click attack buttons and
                                            │ watch the trust gauges drop and isolate malicious nodes in real time!
   docs/novelty_proof_and_defense.md        │ Academic Defense Document: Detailed mathematical formulas, confusion matrices, and formal answers to
                                            │ professor inquiries.
  ──────
   Part 6: Teacher Defense Cheatsheet (Expected Questions & Model Answers)

  Memorize or keep these 4 answers handy:

### Q1: "Why do we need Machine Learning here? Why can't we just use AES encryption?"

  │ Answer:
  │ "Encryption guarantees that outside hackers can't eavesdrop on packets. But in unattended sensor fields, attackers can physically steal a sensor or
  │ exploit its firmware to extract the secret AES keys. Once corrupted, this node is an Insider Threat—its cryptographic checks pass 100% of the time,
  │ but its code silently deletes packets from memory before sending them. Encryption cannot verify whether a node actually executes its forwarding
  │ duties; only behavioral observation and ML can."

### Q2: "Why didn't you use Deep Learning or Neural Networks?"

  │ Answer:
  │ "Sensor nodes and IoT gateways have severe constraints: small microcontrollers (like ARM Cortex-M or 8-bit AVR), tiny RAM (8–64 KB), and strictly
  │ limited battery power. Deep neural networks require high computational power, GPU acceleration, and introduce latency. Random Forest runs in 0.0039
  │ milliseconds per packet, uses minimal memory, and allows us to inspect exactly why decisions were made via Gini feature importance."

### Q3: "How do you know your model didn't just overfit (memorize the data)?"

  │ Answer:
  │ "We used an 80/20 stratified train/test split. The model was evaluated on 16,000 completely unseen records that it had never encountered during
  │ training. It achieved 99.62% overall accuracy and 99.38% recall on Grayhole attacks on that held-out test set."

### Q4: "What is the exact novelty of your project?"

  │ Answer:
  │ "Detecting Blackhole and Flooding attacks is relatively trivial because their packet spikes or total drops are extreme. Our novelty is solving
  │ Grayhole (Selective Forwarding) detection in noisy wireless environments. By integrating mathematical Direct Trust and Composite Trust into the
  │ feature space, we gave the Random Forest the exact signal needed to separate deliberate partial packet drops from natural wireless collisions,
  │ eliminating 74% of missed attacks."
  ──────
   Part 7: How to Run the Demo for Your Teacher

  To give a live demo on your screen:

1. Open your terminal in the workspace:
   cd /home/aditya-2274/terf_deliverable
   python3 frontend/server.py 8000
2. Open your web browser to http://localhost:8000.
3. Show them:
   • Click Grayhole on the attack panel.
   • Show how the Direct Trust and Composite Trust gauges drop.
   • Adjust the Severity Slider (1 to 10) to show how the model adapts to aggressive vs subtle attacks.
   • Show the Active Quarantine status automatically switching from Authorized → Suspicious → Isolated Malicious Node.

────────────────────────────────────────────────────────────

> give me curated list of topics to study like i don't have problem in terminologies, and yt crash course would or andrew ng course, whatever you think
> would be fine

▸ Thought for 10s

  Here is a curated, high-yield study list specifically tailored to the algorithms, metrics, and workflows used in this project.

  Instead of wading through a 40-hour course, these are the exact 5 core topics you need, along with the best YouTube videos (StatQuest & Andrew Ng)
  that explain the math and intuition with zero fluff.
  ──────

### Total Watch Time: ~2.5 Hours

  ┌───────────────────────┐   ┌───────────────────────┐
  │                       │   │                       │
  │ T1["1. Decision Trees │   │     T2["2. Random Forests     │
  │                       ├─┬►│                               │
  │        (Splits        │ │ │            (Bagging            │ │ │                   │
  │                       │ │ │                                │ │ │                   │
  └───────────┬───────────┘ │ └────────────────────────────────┘ │ └───────────────────┘
              │             │                                    │
              ├─────────────┤                                    │
  ┌───────────────────────┐ │ ┌────────────────────────────────┐ │ ┌───────────────────┐
  │           ┴           │ │ │                                │ │ │                   │
  │        Gini)"]        ├─┴►│         Out-of-Bag)"]          │ │ │  Stratification"] │
  │                       │   │                                │ │ │                   │
  └───────────────────────┘   └────────────────────────────────┘ │ └───────────────────┘
                                                                 │           ▲
                                               ┌─────────────────┘           │
  ┌───────────────────────┐   ┌────────────────────────────────┐             │
  │                       │   │                ┴               │             │
  │                       │   │   3. Classification Metrics    │             │
  │           T2          ├──►│                                ├─────────────┘
  │                       │   │ (Confusion Matrix, Recall, F1) │
  │                       │   │                                │
  └───────────────────────┘   └────────────────────────────────┘
  ┌───────────────────────┐   ┌────────────────────────────────┐
  │                       │   │                                │
  │                       │   │     5. Feature Importance      │
  │           T4          ├──►│                                │
  │                       │   │   (Gini Impurity Reduction)    │
  │                       │   │                                │
  └───────────────────────┘   └────────────────────────────────┘
  ──────

## Topic 1: Decision Trees (How the Building Blocks Work)

### What to learn:

  • How a tree chooses where to split a feature (e.g., why DATA_F < 10 is chosen instead of DATA_F < 50).
  • Gini Impurity vs. Entropy (measures of "messiness" or how mixed the classes are in a branch).
  • Overfitting: Why a single decision tree is prone to memorizing training data.

### Why your teacher will ask:

  │ "Your project uses a Random Forest. Can you explain how an individual decision tree decides to split a node on Direct Trust?"

### Recommended Resources:

1. StatQuest with Josh Starmer — Decision Trees https://www.youtube.com/watch?v=7VeUPuFGJHk (~17 mins)
   (The single best visual explanation on the internet. Uses step-by-step cartoon graphics).
2. Andrew Ng (DeepLearning.AI) — Decision Tree Learning & Measuring Purity (Information Gain) https://www.youtube.com/watch?v=kYv9G_q_5B0 (~15 mins)
   (From Course 2, Week 4 of his Machine Learning Specialization).
   ──────

## Topic 2: Random Forests & Ensemble Learning

### What to learn:

  • Ensemble Learning: The idea that combining predictions from multiple models yields better results than any single model.
  • Bagging (Bootstrap Aggregation): How each tree is trained on a random sample of rows with replacement.
  • Feature Subsampling: Why each tree only looks at a random subset of features at each split (so dominant features don't take over every single tree).
  • Voting: How all 60 trees cast a majority vote to decide the class (Normal, Grayhole, etc.).

### Why your teacher will ask:

  │ "Why did your Random Forest outperform your Decision Tree? What does the 'Random' part actually randomize?"
  │ (Answer: It randomizes both the data rows sampled and the subset of features chosen at each split).

### Recommended Resources:

1. StatQuest with Josh Starmer — Random Forests Part 1: Building, Using and Evaluating https://www.youtube.com/watch?v=J4Wdy0Wc_xQ (~10 mins)
2. Andrew Ng (DeepLearning.AI) — Using Multiple Decision Trees (Random Forest) https://www.youtube.com/watch?v=k9a_g2TuhvE (~12 mins)
   ──────

## Topic 3: Evaluation Metrics (Precision, Recall, F1-Score & Confusion Matrix)

### What to learn:

  • Confusion Matrix: True Positives (TP), True Negatives (TN), False Positives (FP), and False Negatives (FN).
  • Accuracy vs. Recall: Why 99% accuracy is misleading if an attack class is small, and why Recall (Sensitivity) is the most critical metric for
  cyberattacks.
  • Macro vs. Weighted F1-Score: How multi-class averages work across your 5 classes.
  • Type I Error (False Alarm) vs. Type II Error (Missed Attack).

### Why your teacher will ask:

  │ "Why do you emphasize Grayhole Recall (99.38%) over overall Accuracy (99.62%)?"
  │ (Answer: Because in cybersecurity, missing a stealth attack—a False Negative—lets the attacker stay in the network. Recall specifically measures how
  │ many actual attacks were caught).

### Recommended Resources:

1. StatQuest with Josh Starmer — Confusion Matrix, Sensitivity (Recall), and Specificity https://www.youtube.com/watch?v=Kdsp6soqA7o (~12 mins)
2. StatQuest with Josh Starmer — Precision and Recall clearly explained https://www.youtube.com/watch?v=j-EB6RqqjGI (~6 mins)
3. Andrew Ng (DeepLearning.AI) — Precision, Recall, and the F1-Score https://www.youtube.com/watch?v=W5ptB1q_j6M (~10 mins)
   ──────

## Topic 4: Data Splitting, Stratification & Overfitting

### What to learn:

  • Train / Test Split: Why we train on 80% (64,000 rows) and evaluate on 20% (16,000 held-out rows).
  • Stratified Sampling (stratify=y): Ensuring that the 20% test set has the exact same percentage of each attack type as the training set, so rare
  attacks aren't underrepresented.
  • Data Leakage: Why you must never let test data touch the model during training.

### Why your teacher will ask:

  │ "How did you split your data? Did you use random split or stratified split, and why does that matter for class imbalance?"

### Recommended Resources:

1. StatQuest with Josh Starmer — Cross Validation & Train/Test Splits https://www.youtube.com/watch?v=fSytzGwwBVw (~10 mins)
2. Andrew Ng (DeepLearning.AI) — Training, Cross Validation, and Test Sets https://www.youtube.com/watch?v=_vdXTe_1Q6I (~11 mins)
   ──────

## Topic 5: Feature Importance & Feature Engineering

### What to learn:

  • Feature Engineering: Creating new mathematical features from domain knowledge (e.g., creating Direct_Trust = DATA_F / DATA_R from raw counters).
  • Gini Importance (Mean Decrease in Impurity - MDI): How scikit-learn calculates which features contributed most to reducing classification errors
  across all 60 trees.
  • Why Random Forest doesn't require feature scaling (normalization/standardization), whereas models like Logistic Regression or SVM do.

### Why your teacher will ask:

  │ "How do you prove that your Trust scores actually helped, rather than the model just using the raw packet counters?"
  │ (Answer: We inspected Gini Feature Importance—Direct_Trust [22.7%] and Composite_Trust [18.9%] ranked #1 and #2 overall, proving the model actively
  │ prioritized them).

### Recommended Resources:

1. StatQuest with Josh Starmer — Feature Importance and How Random Forests Rank Variables https://www.youtube.com/watch?v=sQ870aTKqiM (~8 mins)
   ──────

## Quick Study Roadmap (2-Evening Plan)

   Session            │ What to Watch / Read                                           │ Target Takeaway
  ────────────────────┼────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────
   Evening 1 (60 min) │ • StatQuest: Decision Trees• StatQuest: Random Forests Part 1• │ Understand how trees split using Gini Impurity and how 60
                      │ Andrew Ng: Using Multiple Decision Trees                       │ trees vote together.
   Evening 2 (60 min) │ • StatQuest: Confusion Matrix, Precision, Recall• StatQuest:   │ Understand why Recall matters for Grayhole and how our
                      │ Feature Importance• Review results/cyberattack_report.txt      │ confusion matrix proves the novelty.

  │ Tip
  │ If you only have 1 hour total: Watch StatQuest: Decision Trees, StatQuest: Random Forests, and StatQuest: Precision and Recall. Josh Starmer's
  visual
  │ style makes these concepts stick instantly without any confusing calculus.

───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

## Part 8: Hardware Reality — Motes, How Attackers Compromise Them, and Why TERF Matters

### 1. What Are Microcontrollers, Battery-Powered Sensor Nodes, and IoT Motes?

When people hear "cyberattack," they usually picture a laptop, a web browser, a phishing email, or a `.exe` virus. **Sensor nodes (IoT motes)** have none of those.

As summarized in `docs/novelty_proof_and_defense.md`, devices like **MicaZ** or **TI CC2650** are tiny, matchbox-sized circuit boards left outdoors in unattended places—forests (wildfire detection), farms (soil moisture), bridges (structural monitoring), or industrial plants:

* **Microcontroller (MCU):** Instead of gigabytes of RAM and a multi-GHz CPU, a mote runs on a tiny chip—for instance, **4 KB RAM** on a MicaZ (8-bit ATmega128L) or **20 KB RAM** on a CC2650 (ARM Cortex-M3). It has no Windows/Linux, no browser, and no antivirus; it runs minimal bare-metal C firmware (e.g., TinyOS or Contiki-NG) in a tight loop: *wake up → sense → send/forward radio packet → sleep*.
* **Battery-Powered:** Motes run on small batteries (modeled with a `2.0 J` initial budget in `pipeline/01_simulate_wsn_traffic.py`). Transmitting over the radio uses the most power, so nodes sleep whenever possible and forward data hop-by-hop through a **Cluster Head (`CH`)** toward a **Base Station (Sink)**.

### 2. How Can Attackers Attack Them in the First Place?

Because motes sit exposed outdoors and talk over open radio waves, attackers do not need phishing or malicious email attachments. Instead, they compromise nodes at the **hardware or radio-firmware level** to turn an innocent mote into a **Compromised Insider**:

1. **Physical Node Capture & Key Extraction (Most Common):**
   Low-cost motes lack expensive tamper-proof secure chips. An attacker physically picks up one unattended sensor from the field, connects probes to its exposed debug pins (**JTAG, UART, or SPI**), reads flash memory to extract the network's shared **AES-128 encryption key**, flashes modified C firmware onto it (for example, *"drop 40% of data packets"*), and places it back in the field.
2. **Over-the-Air (OTA) Firmware Exploits:**
   Tiny embedded C stacks generally lack OS memory protections like ASLR or virtual memory. A crafted radio packet that exploits a bug (such as a buffer overflow in packet parsing) can hijack the microcontroller remotely.
3. **Node Cloning (Sybil / Rogue Mote):**
   Once cryptographic keys are pulled from one captured mote, the attacker copies those valid credentials onto unauthorized radio hardware that joins the network as a "trusted" participant.

**Why Encryption Alone Cannot Stop This:**
Once the compromised node holds valid AES-128 keys, every packet it receives and sends **passes cryptographic checks 100%**. Encryption only proves *"this node holds the network key"*—it cannot force the microcontroller CPU to actually forward the decrypted packet instead of deleting it from RAM (`DATA_F = 0`) or flooding the channel with fake control packets.

### 3. Why Detecting "Normal Loss vs. Malicious Attack" Makes a Real Difference

In real Wireless Sensor Networks (WSNs), innocent nodes naturally drop **10%–20% of packets** due to walls, trees, rain/multipath fading, simultaneous radio collisions, or brief queue overflows. Distinguishing natural interference from deliberate sabotage matters enormously in both directions:

* **If you miss an attack (False Negative — calling Grayhole "Normal"):**
  * **Silent telemetry blindness:** A compromised relay dropping 30%–50% of packets causes critical sensor readings (e.g., rising wildfire heat or bridge stress alerts) to vanish quietly without causing an obvious 100% outage.
  * **Network battery death:** In **Flooding** or **Scheduling** attacks, fake `ADV`/`JOIN` broadcasts or out-of-slot transmissions keep innocent neighbors' radios awake and colliding, exhausting finite batteries across the region in days instead of months.
* **If you raise a false alarm (False Positive — calling Normal "Malicious"):**
  * Because the defense response quarantines flagged nodes, panicking during normal wireless interference **bans healthy relay nodes**. Remaining nodes are forced onto longer detours, burn extra battery, and can fracture the network into disconnected islands.

### 4. How Our Project (TERF) Contributes

Consider the classic **Machine Learning Dilemma**:

* **Innocent Node X (busy traffic):** Receives `DATA_R = 200`, drops `DATA_D = 35`, forwards `DATA_F = 165` → **17.5% loss** (plausible wireless collisions).
* **Grayhole Node Y (moderate traffic):** Receives `DATA_R = 70`, drops `DATA_D = 35`, forwards `DATA_F = 35` → **50.0% loss** (deliberate selective dropping).

Both snapshots show the exact same raw drop count (`DATA_D = 35`). A standard classifier looking at raw counters struggles in this overlap zone unless it learns awkward diagonal splits across `DATA_D` and `DATA_R`.

**What TERF contributes in this repository:**

1. **Behavioral Trust Feature Engineering (`pipeline/01_simulate_wsn_traffic.py`):**
   Computes 4 scale-invariant trust features from the 15 LEACH protocol counters:
   * `Direct_Trust = DATA_F / (DATA_R + eps)` (separates Node X's `0.825` from Node Y's `0.50` immediately)
   * `Energy_Trust = Energy / 2.0`
   * `Control_Trust = 1.0 - (control_ratio * 1.6)`
   * `Composite_Trust = 0.50 * Direct_Trust + 0.30 * Control_Trust + 0.20 * Energy_Trust`
2. **Higher Stealth Attack Recall Without Sacrificing Speed (`results/cyberattack_report.txt`):**
   * On the 16,000-row held-out test set, Blackhole, Flooding, and Scheduling already achieve **100.00%** Precision and Recall on all models—**Grayhole** is the real battleground.
   * **Standard Random Forest:** Grayhole Recall = **97.58%**, F1 = **96.71%** (missed **31** of 1,280 Grayhole records).
   * **TERF (Network + Trust Scores):** Grayhole Recall = **99.38%**, F1 = **97.66%** (missed **8** of 1,280 Grayhole records—a **74.2% reduction in missed Grayhole attacks**), with overall accuracy **99.62%**, Normal False Positive Rate **0.47%**, and inference latency **0.0038 ms/sample**.
   * Per `docs/novelty_proof_and_defense.md`, Gini feature importance confirms `Direct_Trust` (`22.73%`) and `Composite_Trust` (`18.94%`) act as the #1 and #2 decision features across the forest.

---

## Part 9: How Would a Normal User Use Our Model? (Real-World End-to-End Architecture)

### 1. Who Is the "Normal User"?

Our training scripts (`pipeline/02_train_and_evaluate_terf.py`) are for developers and researchers, **not** everyday end users. A **normal user** of the finished system is someone like:

* A **smart-farm operator** running soil and irrigation sensors,
* A **forest/wildfire ranger** watching remote environmental motes,
* A **civil/plant engineer** monitoring bridge or factory vibration sensors, or
* An **IT/network technician** overseeing a sensor deployment.

A normal user should **never** have to write Python, understand Gini impurity, or compute trust formulas by hand. To them, TERF should feel like a **plug-and-play "WSN Security Monitor"** that shows green/yellow/red node health and automatically isolates bad nodes.

### 2. Real-World Deployment Architecture (4 Tiers)

Because tiny motes (4–20 KB RAM) cannot run Python or `scikit-learn`, the trained model (`results/terf_model.joblib`) runs one level up—on the **Base Station / Edge Gateway** (such as a Raspberry Pi, industrial edge box, or local server) where sensor traffic converges:

```mermaid
flowchart TD
    subgraph T1 ["1. Field Layer: Tiny Sensor Motes (MicaZ / CC2650)"]
        M1["Sensor Motes collect telemetry & forward packets (LEACH/TDMA)"]
        M2["Neighbors run lightweight Watchdog overhearing<br/>(count DATA_R, DATA_F, DATA_D, ADV/JOIN/SCH, Energy)"]
        M1 --> M2
    end

    subgraph T2 ["2. Edge Gateway / Base Station (Runs results/terf_model.joblib)"]
        G1["Collects periodic 15 raw node counters"] --> G2["Trust Engine auto-computes:<br/>Direct_Trust, Control_Trust, Energy_Trust, Composite_Trust"]
        G2 --> G3["Applies saved StandardScaler + TERF Random Forest<br/>(0.0038 ms/sample prediction)"]
    end

    subgraph T3 ["3. Automated Policy & Quarantine Layer"]
        P1{"Prediction & Composite Trust"}
        P1 -->|"Healthy / High Trust"| A1["NODE AUTHORIZED<br/>(Normal Routing)"]
        P1 -->|"Borderline / Degraded"| A2["SUSPICIOUS<br/>(Reroute Traffic Around Node)"]
        P1 -->|"Attack Confirmed / Trust < 0.38"| A3["MALICIOUS NODE ISOLATED<br/>(Exclude from Topology & Revoke Keys)"]
    end

    subgraph T4 ["4. Normal User Layer (Browser Dashboard & Alerts)"]
        U1["Operator opens http://gateway:8000<br/>Views Green/Yellow/Red gauges, live traffic graphs & plain-English alerts"]
    end

    M2 -->|"Telemetry logs"| G1
    G3 --> P1
    A1 --> U1
    A2 --> U1
    A3 --> U1
```

### 3. Step-by-Step: How a Normal User Uses It

#### A. Behind the Scenes (Automated by the Gateway Using `results/terf_model.joblib`)

When `pipeline/02_train_and_evaluate_terf.py` finishes training, it saves everything needed for prediction into a single file, `results/terf_model.joblib`, containing:

* `'model'`: the trained 60-tree TERF `RandomForestClassifier`
* `'scaler'`: the fitted `StandardScaler`
* `'features'`: the exact 19 expected input column names (15 raw + 4 trust)
* `'classes'`: `['Blackhole', 'Flooding', 'Grayhole', 'Normal', 'Scheduling']`

In a production gateway service (or an exported TinyML/gateway script), whenever a sensor node finishes a reporting round, the software automatically:

1. Reads the node's 15 raw round counters (`Is_CH`, `who_CH`, `Dist_To_CH`, `Rank`, `ADV_S`..`DATA_D`, `Energy`).
2. Computes the 4 trust scores automatically using the exact formulas from `pipeline/01_simulate_wsn_traffic.py`.
3. Feeds the 19 values into the saved model bundle:
   ```python
   import joblib
   import pandas as pd

   bundle = joblib.load("results/terf_model.joblib")
   model = bundle["model"]
   scaler = bundle["scaler"]
   features = bundle["features"]
   classes = bundle["classes"]

   # row_df = 1-row DataFrame containing the 15 raw counters + 4 computed trust scores
   X_scaled = scaler.transform(row_df[features])
   pred_idx = model.predict(X_scaled)[0]
   probs = model.predict_proba(X_scaled)[0]

   label = classes[pred_idx]
   confidence = probs[pred_idx] * 100.0
   ```
4. Returns a plain-English verdict (`Grayhole — 98.6% confidence`) and triggers quarantine if needed.

#### B. What the Normal User Actually Sees & Does

From the user's point of view, using the system takes just 3 simple actions:

1. **Start / Open the Console:** Power on the gateway (or run `python3 frontend/server.py 8000`) and open `http://localhost:8000` in any web browser.
2. **Watch Plain-Language Status (Zero ML Jargon Needed):**
   * **Green (`NODE AUTHORIZED`):** Traffic is normal (even if there is minor wireless interference); no action needed.
   * **Yellow (`SUSPICIOUS - REROUTING`):** Trust is dropping; the network shifts important packets onto safer backup paths while monitoring.
   * **Red (`MALICIOUS NODE ISOLATED`):** Attack confirmed (`Blackhole`, `Grayhole`, `Flooding`, or `Scheduling`); the rogue node is cut out of routing and logged so a technician knows which physical sensor to inspect or replace in the field.
3. **Inspect Live Gauges & Logs:** Check the **Direct Trust** bar (is the node forwarding packets?) and **Control Trust** bar (is it spamming control messages?) plus the timestamped alert log (`Classification: NORMAL → GRAYHOLE`).

### 4. Honest Note: Current Repo State vs. Full Production Deployment

As documented in `follow-up-moves.md`, it is important to be clear about what runs today versus what the next integration step connects:

* **Already built today:** Synthetic WSN-DS traffic generation (`pipeline/01_simulate_wsn_traffic.py`), multi-model training and the serialized `results/terf_model.joblib` artifact (`pipeline/02_train_and_evaluate_terf.py`), and the interactive Security Operations Console (`frontend/server.py` + `frontend/index.html`).
* **How the current UI works:** Right now, `frontend/index.html` uses client-side JavaScript (`sampleStep()`) to simulate live telemetry waveforms and quarantine rules for demonstration.
* **To make it work on real telemetry for a normal user:** Adding a `POST /api/predict` route in `frontend/server.py` that loads `results/terf_model.joblib` (using the `joblib.load` flow above) lets either live gateway feeds or uploaded WSN CSV logs flow directly through the real trained TERF model into the browser console—and validating against the official Kaggle `WSN-DS.csv` confirms performance on NS-2 benchmark traces as well.

───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
