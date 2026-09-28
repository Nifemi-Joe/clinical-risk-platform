# The Simple Version — What We Actually Built and Found

This is the same project as `technical-report.md`, explained without the
jargon. If you can follow this, you can follow the real one too — it's the
same facts, just slower and with more "why does that matter."

---

## 1. What is this thing, in one sentence?

We built a computer program that looks at a patient's health information
(age, blood pressure, cholesterol, etc.) and estimates how likely it is that
they have heart disease — and we built it carefully enough to trust the
answer, not just get *an* answer.

## 2. Why "carefully" is the whole point

Imagine two students grading the same essay:

- **Student A** reads the essay once and gives it a grade.
- **Student B** reads it, checks their notes weren't copied from the answer
  key, tests themselves on a different essay by a different teacher, and
  says "here's my grade, and here's how confident I am, and here's where
  I might be wrong."

Most beginner machine learning projects are Student A: train a model, get a
number like "95% accurate!", done. This project is trying hard to be
Student B. That's slower and less flashy, but it's the difference between
a toy and something you could actually trust.

## 3. Where did the data come from?

Real medical records from four hospitals in the 1980s (Cleveland USA,
Budapest Hungary, Zurich/Basel Switzerland, Long Beach USA), originally
collected by real doctors and donated to a public research archive. Nothing
was made up — we downloaded the actual files and checked the row counts
matched what the archive says they should be, like checking a delivery box
has the right number of items before opening it.

## 4. What did we build, step by step?

**Step 1 — Get the data safely.** We wrote code that loads the hospital
files and does the bare minimum cleanup (turning "?" into "we don't know
this value" instead of guessing).

**Step 2 — Prepare the data without cheating.** This is the most important
"boring" thing we did. Imagine studying for a test: it's cheating if you
peek at the answer key while studying. In machine learning, it's the
equivalent "cheating" to let any information from the *test* patients leak
into how you prepare the *training* patients. We built the preparation step
(filling in missing values, scaling numbers) so it can ONLY ever see the
training patients when it's learning how to prepare data — then it applies
that, unchanged, to the test patients. We even wrote an automatic check
(a "test" in the software sense) that fails loudly if this rule is ever
broken by accident later.

**Step 3 — Try lots of different prediction methods.** We didn't just try
one technique. We tried nine: from very simple (a straight-line rule) to
very fancy (a mini version of the same kind of AI architecture behind
ChatGPT, just much smaller, adapted for spreadsheets of numbers instead of
text). We also always include a "dumbest possible guess" (just always
predict "no disease") as a sanity check — if a fancy model can't beat the
dumb guess, something is badly wrong.

**Step 4 — Grade the models fairly.** We didn't just check "how often is it
right" (that's misleading — see below). We checked several different things
at once, the way a doctor wouldn't judge a test purely on "did it flag
this one patient correctly."

**Step 5 — Test it somewhere new.** We trained only on the Cleveland
hospital's patients, then — without letting the model see any more data or
retrain at all — checked how well it did on patients from the *other three*
hospitals. This is like training a student using only one textbook, then
giving them an exam written by a completely different teacher.

**Step 6 — Explain WHY the model thinks what it thinks.** For any single
patient, we can show which of their health measurements pushed the
prediction up or down, and by how much (using a technique called SHAP).

**Step 7 — Try a second, very different disease.** To prove the system we
built isn't just a one-off script, we plugged in a completely different
dataset (breast cancer) using the *exact same* underlying code, changing
only the list of the dataset's own column names. If it "just worked," that
proves the code is genuinely reusable, not held together with duct tape.

## 5. What did we find? (The honest, real results)

### Finding 1: Within one hospital, several methods work really well

On patients the model hadn't seen before (but from the *same* hospital it
trained on), the best methods correctly separated "has heart disease" from
"doesn't" about 95–96% of the time in a statistical sense (this number is
called ROC-AUC — think of it as "if you show the model one sick patient and
one healthy patient at random, how often does it correctly say the sick one
is riskier?" — 50% would be a coin flip, 100% would be perfect).

### Finding 2: The same model does noticeably WORSE at a different hospital

This is the big one. The exact same model that scored ~95% at its home
hospital dropped to as low as 67–78% when tested on a different hospital's
patients — and its *confidence* (how well its "70% chance" predictions
actually matched reality) got much worse too, not just its accuracy.

**Why this matters, in plain terms:** if you build a health app and only
test it on patients from one clinic, you genuinely do not know how well it
will work on patients somewhere else — different equipment, different
typical patients, different record-keeping habits. This is one of the most
common and most dangerous mistakes people make when building medical AI,
and we didn't just say "be careful about this" — we actually measured it
happening, with real numbers.

### Finding 3: The "best" model at home wasn't the "best" model elsewhere

At the home hospital, the simplest method (a straight-line rule, called
logistic regression) was actually the top performer. But when we averaged
performance across the three *other* hospitals, a different method (Random
Forest, which is like averaging the opinions of hundreds of simpler
decision-tree "mini-experts") did better on average, even though it wasn't
the top performer at home.

**Why this matters:** picking your "winner" only by how well it does on the
data it was trained on is a trap — the model that looks best at home isn't
always the one that will actually work best once it leaves the building.

### Finding 4: We found a subtle statistics trap — and it's a good one to know

One of our scoring methods (PR-AUC) looked *great* on one of the other
hospitals (around 97–98%). Sounds amazing — except at that hospital, 93.5%
of all patients in the data actually had heart disease. If you just guessed
"everyone has it" for every single patient with zero intelligence, you'd
already score about 93.5% on that same measurement. So our model's real,
earned improvement over "just guessing" was much smaller than the headline
number made it look. This is a classic way statistics can accidentally
mislead you if you don't check what the "do-nothing" baseline would score,
and we caught it by actually calculating that baseline rather than assuming.

### Finding 5: Some measurements were suspicious, and the data proved it

Two of the patient measurements (`thal`, from a thallium heart scan, and
`ca`, from an X-ray-like procedure) are actually *outputs of the same
diagnostic process* used to decide if someone has heart disease in the
first place — a bit like using "the doctor ordered a biopsy" as a predictor
of cancer. Before training anything, we flagged this as suspicious. Then,
when we checked which measurements the model relied on most, those exact
two came out on top. The model independently confirmed our suspicion — a
nice example of catching a problem before it becomes a false claim, rather
than after.

### Finding 6: A more "modern AI" model didn't clearly win — and that's fine

We hand-built a scaled-down version of a Transformer (the same family of AI
architecture behind large language models), just made small and adapted for
spreadsheet-style data instead of text. It performed almost as well as the
simplest method — which is actually a bit surprising, because that kind of
architecture is usually expected to need much more data than the ~240
patients we trained it on to work well. We reported this honestly, including
that the result is uncertain (small dataset = noisy results) rather than
claiming a win we can't back up.

### Finding 7: A second disease, same code, worked immediately — with one honest bug

Plugging in breast cancer data through the same reusable system hit one real
bug on the first try: an empty list (because this dataset has zero
"category-style" columns, unlike heart disease's "male/female" type
columns) was accidentally being treated by Python as "nothing was provided,
use the heart-disease defaults instead" — a well-known gotcha in this
programming language. We caught it immediately because the system crashed
loudly instead of silently doing the wrong thing, fixed it, and added a
permanent automatic check so it can never silently happen again. Once fixed,
breast cancer classification worked almost perfectly (99%+) with almost
every method — which, per our plan, was the *expected* result, since this
particular dataset's measurements were specifically designed decades ago to
make this kind of classification easy.

### Finding 8: A real "it doesn't install on my computer" bug — and what it teaches

When this was actually run on a real Intel Mac (not the build sandbox), the
whole installation broke immediately, because one piece we'd added (a
component called "torch," needed only for the experimental Transformer
model) simply refuses to install on Intel Macs anymore — the company that
makes it stopped supporting that kind of computer. This had nothing to do
with our code being wrong; it was a case of one optional ingredient being
bundled in with everything else, so when that one ingredient couldn't be
delivered, the whole recipe failed to even start.

**The fix:** separate the "always needed" ingredients from the "only needed
for one experimental feature" ingredient, and make the program smart enough
to say "I can't do the fancy Transformer part on this computer, but
everything else still works" instead of refusing to run at all. This is a
genuinely good lesson for building real software: one optional, fragile
piece should never be allowed to block everything else from working.

## 6. So... is the model "good"?

The honest answer: **good at the hospital it was trained on, not yet proven
good elsewhere, and not something anyone should use for a real diagnosis.**
That's not a disappointing answer — it's the correct, responsible one, and
getting to state it with actual evidence (not a guess) is the entire value
of doing this properly.

---

## 7. Ways to make this better — concrete, prioritized

Ordered by "biggest improvement in trustworthiness for the effort," not by
build order.

**A. Highest value, do this next**
1. **Test the "modern AI did surprisingly well" result more than once.**
   Right now it's based on a single train/test split. Rerun it with 5–10
   different random splits and see if it's still competitive on average, or
   if we got lucky once. This is the single most important thing left to
   check — an interesting result nobody has stress-tested yet.
2. **Check whether the model is leaning on "cheating" features.** Rerun the
   heart disease comparison with the two suspicious measurements (`thal`,
   `ca`) removed, and see how much the ~95% score drops. This tells us how
   much of the model's apparent skill is genuine risk prediction vs.
   secretly re-detecting "a doctor already suspected something."
3. **Get the diabetes dataset working too**, but be upfront about its
   weaker sourcing (it's a cleaned-up copy of a copy, not straight from the
   government agency) and its very different nature (people's own survey
   answers on the phone, not a doctor's exam).

**B. Makes the whole system more trustworthy**
4. **Try many different random ways of splitting the data**, not just one,
   for every result in this report — so we can say "this held up across 10
   different splits," which is a much stronger claim than "this happened
   once."
5. **Get real predictions checked by someone who understands medicine**,
   even informally — a nurse or doctor sanity-checking "does the model's
   reasoning make clinical sense" is worth more than another statistic.
6. **Try the TabPFN model for real**, once there's a way to get past its
   locked-download requirement — it's specifically designed for small
   datasets like this one and could be a genuinely strong comparison point.

**C. Turns this from "a study" into "a usable thing"**
7. **Build the actual website/app** where someone can enter numbers and see
   a prediction, with the explanation ("why did it say this?") shown
   clearly, and a big, unmissable reminder that this is not a real
   diagnosis.
8. **Put it online somewhere real** (an actual working link), not just code
   sitting on a hard drive — this is the single biggest thing that makes a
   project believable to someone looking at it from the outside.
9. **Write the short, friendly version of this report** (this document) as
   the front page, and put the detailed version behind a link — most
   people deciding whether your work is impressive will read the first
   thing they see, not the fifth.

**D. Nice to have, not urgent**
10. Add the third gradient-boosting method (CatBoost) mentioned in the
    original plan but skipped so far — unlikely to change the story much,
    good for completeness.
11. Try more thorough automatic tuning (a wider, more exhaustive search for
    each model's best settings) now that the basic version is proven to
    work — likely small gains, but a nice polish step once everything else
    above is done.

---

## 8. What about diabetes and the actual website?

We finished those too. Quick summary in plain terms:

**Diabetes:** we found something even more dramatic than the heart disease
findings. One of our models (Random Forest, left on default settings) got a
totally respectable-looking overall score — but when we checked how many
*actual* diabetic patients it correctly identified, the answer was 0.5%.
Not 50%. Half of one percent. It was basically always guessing "no
diabetes" and getting away with it because most people in the data don't
have diabetes, so guessing "no" is usually right. The overall score didn't
catch this at all — you had to check the right thing (how many sick people
did it actually catch) to see the problem. We fixed it with a setting that
tells the model "pay extra attention to the rare category," which jumped it
from catching 0.5% of diabetics to catching 77% of them (at the cost of a
few more false alarms — a trade worth making for a screening tool). This is
probably the single clearest "gotcha" in the whole project, and a great
one to know if you ever build anything with a rare outcome (fraud
detection, disease screening, defect detection — all the same trap).

**The actual website (API):** we built and tested a real, working backend
that you could type patient numbers into and get a prediction back — tested
with real, actual requests, not just "the code looks right." One nice
detail: for the heart disease and diabetes screening tools, we deliberately
did NOT pick the model with the single highest score to actually serve to
users — we picked the ones that behave sensibly in practice (generalizes to
new hospitals; actually catches sick patients), because a model that
"scores best" on paper but fails at the actual job is a bad choice, however
good the number looks on a slide.

**What's still missing:** an actual visual website (right now it's just the
backend "brain" — a person would need the visual front-end part built next
to type in numbers through a nice screen), and putting it on the internet
somewhere with a real address anyone can visit.

---

## 9. Closing the gaps — in plain terms

**Forgot your password?** Now works for real, and it's built the careful
way: the link that gets emailed only works for resetting a password (not
for logging in as that person), only works once, and expires in 30
minutes. We tested this by actually trying to break it — using a login
token to try to reset a password (correctly blocked) and checking that
asking for a reset on an email that doesn't exist gives the exact same
response as one that does (so nobody can use this page to check who has an
account).

**Making the app load faster.** The whole app used to download as one big
594 KB file before showing anything. Now it downloads about 8 KB first and
fetches the rest of each page only when you actually visit it — the heavy
chart-drawing code, for instance, only loads if you go to the pages with
charts. We didn't just assume this helped — we rebuilt it and actually
measured the new file sizes.

**Testing the website itself, not just the backend.** Up to now, every test
was checking the "brain" (the Python backend). Now there are 13 real tests
checking the actual website code too — does logging in correctly update
what the screen shows, does logging out actually clear things, does a
high-risk result look visually different from a low-risk one. Setting this
up hit a real snag (two tools wanted different, incompatible versions of a
third tool) that we had to sort out — normal, ordinary software friction,
now resolved.

**A round of cleanup.** Running a code-quality checker for the first time
against everything we'd built so far found 98 small leftover issues —
things like an import we added early on and then stopped using. None of
them were bugs exactly, more like leftover clutter from moving fast across
seven phases. Cleaned it all up and re-ran every test afterward to make
sure the cleanup itself didn't break anything.

**Getting this onto the actual internet.** This is the one part I genuinely
can't finish for you — putting a website on a real, public web address
needs someone's own account with a hosting company (and usually a payment
method on file), and I can't create accounts or agree to terms on your
behalf. What I did instead: wrote out the exact, step-by-step instructions
for three different hosting options, so it's a "follow these copy-paste
steps" job rather than a "figure out how deployment works" job.

## Finding 9: the "why did it say that" report was basically unreadable

You sent a screenshot of the app after a prediction, and it was a fair
complaint: the "what influenced this estimate" list was showing things
like `cat__thal_7.0  -0.049` and `cat__thal_3.0  -0.058`. That's the
computer's internal name for a category, not something a person — patient
or doctor — could read. Worse, for the heart-disease model specifically,
the *reason* both of those showed up together is a genuinely confusing
technical wrinkle: the method used to explain that model's decisions
(called SHAP) can put a number next to a category the patient doesn't even
have, because of how it does its math. So it wasn't just "translate the
labels," it was "the two numbers on screen looked like they contradicted
each other, and they kind of did, for a reason worth actually fixing."

What changed:

1. **Combined the pieces back into one real-world question.** "Thalassemia
   test result" is one thing a patient answers, even though the computer
   internally splits it into three yes/no columns. Now all three get added
   back together into a single number before anything is shown, so you see
   one row for "Thalassemia test result: Normal" instead of two
   contradictory-looking fragments.
2. **Every row now says what the patient's actual answer was, in plain
   English.** Not "thal = 3", but "Thalassemia test result — Normal,
   decreased risk, moderate effect."
3. **Added a "how this report was generated" section you can open.** It
   names the exact model used, why that model was picked over the
   alternatives (reusing the real comparison numbers from earlier phases,
   not a new made-up justification), exactly how the influence numbers
   were calculated, what data it was trained on, and — importantly — what
   this specific method can't tell you (e.g. a straight-line model like
   the ones used for diabetes/breast cancer can't capture "this only
   matters when combined with that").

Checked for real afterward: all 24 backend tests still pass, the frontend
type-checker is clean, all 15 frontend tests pass (including a rewritten
one that now specifically checks the old raw codes do NOT appear anymore),
and the production build still works.
