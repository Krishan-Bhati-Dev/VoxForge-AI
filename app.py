
import os
import re
import asyncio
import tempfile

import streamlit as st
import edge_tts

from firecrawl import FirecrawlApp
from openai import OpenAI
from pydub import AudioSegment


# ============================================================
# CONFIG
# ============================================================

APP_TITLE = "📰 → 🎙️ Blog to Podcast AI Studio"

OPENROUTER_MODELS = [
    "qwen/qwen3.8-27b:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "poolside/laguna-s-2.1:free",
]

EXPECTED_TURNS = 8

MIN_SCRIPT_CHARS = 700
MAX_SCRIPT_CHARS = 1800

MAX_ARTICLE_CHARS = 18000

FFMPEG_PATH = (
    r"C:\ffmpeg-9.0.2-essentials_build\bin\ffmpeg.exe"
)


# ============================================================
# EDGE TTS VOICES
# ============================================================

VOICES = {
    "English": {
        "Alex": "en-IN-PrabhatNeural",
        "Sam": "en-IN-NeerjaNeural",
    },
    "Hindi": {
        "Alex": "hi-IN-MadhurNeural",
        "Sam": "hi-IN-SwaraNeural",
    },
}


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🎙️",
    layout="wide",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main {
        background: #0b1020;
    }

    .block-container {
        padding-top: 2rem;
        max-width: 1250px;
    }

    .hero {
        padding: 25px;
        border-radius: 20px;
        background: linear-gradient(
            135deg,
            #111936,
            #18234a
        );
        border: 1px solid #2b3b70;
        margin-bottom: 25px;
    }

    .hero h1 {
        font-size: 42px;
        margin-bottom: 8px;
    }

    .hero p {
        color: #aeb9d8;
        font-size: 17px;
    }

    .card {
        padding: 20px;
        border-radius: 16px;
        background: #11182e;
        border: 1px solid #293657;
        margin-bottom: 15px;
    }

    .speaker-alex {
        padding: 15px;
        border-radius: 14px;
        background: #172342;
        border-left: 4px solid #5b8cff;
        margin-bottom: 10px;
    }

    .speaker-sam {
        padding: 15px;
        border-radius: 14px;
        background: #211c39;
        border-left: 4px solid #b579ff;
        margin-bottom: 10px;
    }

    .small {
        color: #9ca9c9;
        font-size: 13px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPERS
# ============================================================

def clean_text(text):
    if not text:
        return ""

    text = re.sub(r"\s+", " ", str(text))
    return text.strip()


def normalize_url(url):
    url = url.strip()

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    return url


# ============================================================
# FIRECRAWL
# ============================================================

def scrape_article(api_key, url):

    if not api_key:
        raise RuntimeError(
            "Firecrawl API key is missing."
        )

    app = FirecrawlApp(
        api_key=api_key
    )

    try:

        result = app.scrape_url(
            url,
            formats=["markdown"]
        )

    except TypeError:

        # Compatibility with different SDK versions
        result = app.scrape(
            url,
            formats=["markdown"]
        )

    markdown = ""

    if isinstance(result, dict):

        markdown = (
            result.get("markdown")
            or result.get("content")
            or ""
        )

    else:

        markdown = getattr(
            result,
            "markdown",
            ""
        )

        if not markdown:

            markdown = getattr(
                result,
                "content",
                ""
            )

    markdown = clean_text(markdown)

    if len(markdown) < 500:

        raise RuntimeError(
            "Firecrawl could not extract enough article content. "
            "Try another article URL."
        )

    return markdown[:MAX_ARTICLE_CHARS]


# ============================================================
# OPENROUTER
# ============================================================

def create_openrouter_client(api_key):

    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        default_headers={
            "HTTP-Referer": "http://localhost:8501",
            "X-Title": "Blog to Podcast AI",
        },
    )


def extract_response_text(response):

    try:

        content = response.choices[0].message.content

        if content:
            return content.strip()

    except Exception:
        pass

    return ""


# ============================================================
# AI CONTENT GENERATION
# ============================================================

def generate_ai_content(
    api_key,
    article,
    language
):

    client = create_openrouter_client(
        api_key
    )

    prompt = f"""
You are an expert conversational podcast writer.

Transform the article below into a SHORT, NATURAL and
ENGAGING conversation between two podcast hosts: Alex and Sam.

The result must FEEL like a real podcast, not like two people
reading an article or taking turns answering questions.

LANGUAGE:
{language}

CORE GOAL:

Create the feeling that Alex and Sam are sitting together
in a podcast studio and genuinely discussing the topic.

They must listen to each other, react to each other's points,
show curiosity, and naturally move the conversation forward.

--------------------------------------------------
NATURAL CONVERSATION
--------------------------------------------------

Alex and Sam should:

- sound like real intelligent people
- greet naturally at the beginning
- introduce the topic conversationally
- acknowledge what the other person just said
- react to interesting or surprising information
- sometimes ask meaningful follow-up questions
- sometimes make observations
- connect every response to the previous line
- show curiosity and personality
- explain technical information simply
- vary sentence structure
- use natural spoken language
- use contractions such as "it's", "that's", "we're", "I've"

Natural reactions may include:

"Exactly."

"Right."

"That's interesting."

"Wait, seriously?"

"Yeah, that's the interesting part."

"I was wondering about that too."

"That actually makes sense."

"That's a good point."

Do not overuse these phrases.

--------------------------------------------------
DO NOT SOUND LIKE THIS
--------------------------------------------------

Do NOT make the conversation:

- a textbook
- a news article being read aloud
- a list of facts
- a classroom lecture
- an interview questionnaire
- eight unrelated statements
- robotic
- overly formal
- repetitive

Do NOT make every Sam line a question.

Do NOT make every Alex line an explanation.

Do NOT simply copy facts from the article one after another.

--------------------------------------------------
PODCAST FLOW
--------------------------------------------------

There must be EXACTLY 8 dialogue turns.

Turn 1 — Alex:
Start with a natural podcast greeting and an interesting hook.

Turn 2 — Sam:
Naturally acknowledge Alex and show curiosity or reaction.

Turn 3 — Alex:
Explain the first important idea while connecting it to Sam.

Turn 4 — Sam:
React naturally and ask a meaningful follow-up OR make
an interesting observation.

Turn 5 — Alex:
Add an important example, detail, comparison or implication.

Turn 6 — Sam:
React and add another perspective or meaningful question.

Turn 7 — Alex:
Explain the main takeaway for the listener.

Turn 8 — Sam:
React naturally and CLOSE THE PODCAST.

The final Sam line must sound like a genuine podcast ending.

--------------------------------------------------
STRICT DIALOGUE COUNT
--------------------------------------------------

THIS IS EXTREMELY IMPORTANT.

Generate EXACTLY 8 dialogue lines.

The speaker order MUST be:

Alex
Sam
Alex
Sam
Alex
Sam
Alex
Sam

There must be exactly:

4 Alex lines
4 Sam lines

STOP immediately after the 8th line.

NEVER generate a 9th line.

NEVER generate a 10th line.

Do not continue the conversation after the final Sam line.

--------------------------------------------------
DIALOGUE LENGTH
--------------------------------------------------

The complete SCRIPT should contain approximately
700 to 1600 characters.

Keep each line reasonably concise.

Prioritize natural conversation over unnecessary length.

--------------------------------------------------
OUTPUT FORMAT
--------------------------------------------------

Return EXACTLY:

LANGUAGE: {language}

ANALYSIS:
2-4 concise sentences explaining the main topic.

SCRIPT:
Alex: ...
Sam: ...
Alex: ...
Sam: ...
Alex: ...
Sam: ...
Alex: ...
Sam: ...

Do not use markdown code fences.

Do not add anything after the final Sam line.

Do not output reasoning or thinking.

--------------------------------------------------
ARTICLE
--------------------------------------------------

{article}
"""

    errors = []

    for model in OPENROUTER_MODELS:

        try:

            response = (
                client
                .chat
                .completions
                .create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a professional "
                                "conversational podcast writer. "
                                "Return only the requested final answer. "
                                "Never output chain-of-thought "
                                "or hidden reasoning."
                            ),
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                    temperature=0.25,
                    max_tokens=1400,
                )
            )

            text = extract_response_text(
                response
            )

            if text:

                return text, model

            errors.append(
                f"{model}: empty response"
            )

        except Exception as e:

            errors.append(
                f"{model}: {str(e)[:250]}"
            )

    raise RuntimeError(
        "OpenRouter could not generate the podcast.\n\n"
        + "\n".join(errors)
    )


# ============================================================
# PARSER
# ============================================================

def parse_script_lines(script):

    lines = []

    # Only parse after SCRIPT:
    if "SCRIPT:" in script:

        script = script.split(
            "SCRIPT:",
            1
        )[1]

    for raw_line in script.splitlines():

        line = raw_line.strip()

        if not line:
            continue

        match = re.match(
            r"^(Alex|Sam)\s*:\s*(.+?)\s*$",
            line,
            re.IGNORECASE
        )

        if not match:
            continue

        speaker = match.group(1).capitalize()

        text = match.group(2).strip()

        if text:

            lines.append(
                {
                    "speaker": speaker,
                    "text": text
                }
            )

    return lines


# ============================================================
# NORMALIZE DIALOGUE
# ============================================================

def normalize_dialogue(lines):

    # Already correct
    if len(lines) == EXPECTED_TURNS:

        return lines

    # AI sometimes generates 9, 10 or more lines.
    #
    # We preserve:
    # 1. The first 7 lines -> opening + conversation
    # 2. The LAST line -> natural closing
    #
    # This gives exactly 8 turns.

    if len(lines) > EXPECTED_TURNS:

        first_seven = lines[:7]

        last_line = lines[-1]

        candidate = first_seven + [last_line]

        expected = [
            "Alex",
            "Sam",
            "Alex",
            "Sam",
            "Alex",
            "Sam",
            "Alex",
            "Sam",
        ]

        actual = [
            item["speaker"]
            for item in candidate
        ]

        if actual == expected:

            return candidate

    return lines


# ============================================================
# VALIDATION
# ============================================================

def validate_script(raw_script):

    if not raw_script:

        return (
            False,
            "Script is empty.",
            [],
        )

    script = raw_script.strip()

    # Remove code fences if model adds them
    script = re.sub(
        r"```(?:text)?",
        "",
        script,
        flags=re.IGNORECASE,
    )

    script = script.replace(
        "```",
        ""
    ).strip()

    forbidden = [
        "[...]",
        "…",
        "[text]",
        "<text>",
        "tbd",
        "todo",
        "insert dialogue",
        "insert text",
        "write dialogue here",
        "thinking process",
        "chain of thought",
    ]

    lower_script = script.lower()

    for word in forbidden:

        if word in lower_script:

            return (
                False,
                f"Invalid content detected: {word}",
                [],
            )

    # Parse
    lines = parse_script_lines(
        script
    )

    # IMPORTANT:
    # Automatically normalize 9/10+ AI turns.
    lines = normalize_dialogue(
        lines
    )

    # Exact count
    if len(lines) != EXPECTED_TURNS:

        return (
            False,
            (
                f"Expected exactly "
                f"{EXPECTED_TURNS} dialogue turns, "
                f"but received {len(lines)}."
            ),
            lines,
        )

    expected = [
        "Alex",
        "Sam",
        "Alex",
        "Sam",
        "Alex",
        "Sam",
        "Alex",
        "Sam",
    ]

    actual = [
        item["speaker"]
        for item in lines
    ]

    if actual != expected:

        return (
            False,
            (
                "Invalid speaker order.\n"
                f"Expected: {expected}\n"
                f"Received: {actual}"
            ),
            lines,
        )

    # Total dialogue characters
    total_chars = sum(
        len(item["text"])
        for item in lines
    )

    if total_chars < MIN_SCRIPT_CHARS:

        return (
            False,
            (
                f"Script is too short: "
                f"{total_chars} characters."
            ),
            lines,
        )

    if total_chars > MAX_SCRIPT_CHARS:

        return (
            False,
            (
                f"Script is too long: "
                f"{total_chars} characters."
            ),
            lines,
        )

    # Individual line validation
    for i, item in enumerate(
        lines,
        start=1
    ):

        if len(item["text"]) < 25:

            return (
                False,
                (
                    f"Dialogue line {i} "
                    f"is too short."
                ),
                lines,
            )

    return (
        True,
        "Script validated successfully.",
        lines,
    )


# ============================================================
# ANALYSIS EXTRACTION
# ============================================================

def extract_analysis(raw_text):

    match = re.search(
        r"ANALYSIS:\s*(.*?)(?=SCRIPT:)",
        raw_text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if match:

        return clean_text(
            match.group(1)
        )

    return (
        "AI analysis was generated successfully."
    )


# ============================================================
# EDGE TTS
# ============================================================

async def generate_edge_line(
    text,
    voice,
    output_path,
):

    communicator = edge_tts.Communicate(
        text=text,
        voice=voice,
    )

    await communicator.save(
        output_path
    )


async def generate_edge_all(
    lines,
    language,
    temp_dir,
):

    generated_files = []

    for index, item in enumerate(
        lines,
        start=1,
    ):

        speaker = item["speaker"]

        text = item["text"]

        voice = VOICES[
            language
        ][speaker]

        output_path = os.path.join(
            temp_dir,
            f"line_{index}.mp3",
        )

        await generate_edge_line(
            text,
            voice,
            output_path,
        )

        generated_files.append(
            output_path
        )

    return generated_files


def generate_podcast_audio(
    lines,
    language,
):

    if not os.path.exists(
        FFMPEG_PATH
    ):

        raise RuntimeError(
            "FFmpeg was not found at:\n"
            + FFMPEG_PATH
        )

    AudioSegment.converter = FFMPEG_PATH

    with tempfile.TemporaryDirectory() as temp_dir:

        files = asyncio.run(
            generate_edge_all(
                lines,
                language,
                temp_dir,
            )
        )

        final_audio = AudioSegment.empty()

        # Natural short pause between speakers
        pause = AudioSegment.silent(
            duration=350
        )

        for file_path in files:

            segment = AudioSegment.from_file(
                file_path,
                format="mp3",
            )

            final_audio += segment
            final_audio += pause

        final_path = os.path.join(
            temp_dir,
            "podcast.mp3"
        )

        final_audio.export(
            final_path,
            format="mp3",
            bitrate="128k",
        )

        with open(
            final_path,
            "rb"
        ) as f:

            return f.read()


# ============================================================
# UI - HERO
# ============================================================

st.markdown(
    """
    <div class="hero">

        📰 → 🎙️ Blog to Podcast AI

        
        Turn any article into a conversational AI podcast
        using Firecrawl, OpenRouter and free Edge TTS.
        

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("⚙️ Configuration")

    firecrawl_key = st.text_input(
        "🔥 Firecrawl API Key",
        type="password",
        placeholder="fc-...",
    )

    openrouter_key = st.text_input(
        "🤖 OpenRouter API Key",
        type="password",
        placeholder="sk-or-...",
    )

    st.divider()

    language = st.selectbox(
        "🎙️ Podcast Language",
        [
            "English",
            "Hindi",
        ],
    )

    st.info(
        "🎧 TTS: Edge TTS\n\n"
        "Free and does not consume "
        "your ElevenLabs credits."
    )

    st.divider()

    st.caption(
        "Blog → Firecrawl → AI → TTS → MP3"
    )


# ============================================================
# MAIN INPUT
# ============================================================

st.subheader("🔗 Enter Article")

url = st.text_input(
    "Blog / Article URL",
    placeholder="https://example.com/article",
)

generate_button = st.button(
    "🚀 Generate Podcast",
    type="primary",
    use_container_width=True,
)


# ============================================================
# GENERATION
# ============================================================

if generate_button:

    if not firecrawl_key:

        st.error(
            "Please enter your Firecrawl API key."
        )

        st.stop()

    if not openrouter_key:

        st.error(
            "Please enter your OpenRouter API key."
        )

        st.stop()

    if not url:

        st.error(
            "Please enter an article URL."
        )

        st.stop()

    url = normalize_url(
        url
    )

    progress = st.progress(0)

    status = st.empty()

    try:

        # ====================================================
        # STEP 1
        # ====================================================

        status.info(
            "🔥 Step 1/4 — Extracting article..."
        )

        progress.progress(10)

        article = scrape_article(
            firecrawl_key,
            url,
        )

        progress.progress(25)

        # ====================================================
        # STEP 2
        # ====================================================

        status.info(
            "🤖 Step 2/4 — Generating AI podcast..."
        )

        raw_ai_output, used_model = (
            generate_ai_content(
                openrouter_key,
                article,
                language,
            )
        )

        progress.progress(50)

        # ====================================================
        # STEP 3
        # ====================================================

        status.info(
            "🧠 Step 3/4 — Validating dialogue..."
        )

        valid, message, dialogue = (
            validate_script(
                raw_ai_output
            )
        )

        if not valid:

            st.error(
                "Script validation failed:\n\n"
                + message
            )

            with st.expander(
                "Show AI response"
            ):

                st.text(
                    raw_ai_output
                )

            progress.empty()

            st.stop()

        progress.progress(65)

        # ====================================================
        # STEP 4
        # ====================================================

        status.info(
            "🎙️ Step 4/4 — Creating podcast audio..."
        )

        audio_bytes = (
            generate_podcast_audio(
                dialogue,
                language,
            )
        )

        progress.progress(100)

        status.success(
            "✅ Podcast generated successfully!"
        )

        # ====================================================
        # SESSION STATE
        # ====================================================

        st.session_state["article"] = article

        st.session_state["analysis"] = (
            extract_analysis(
                raw_ai_output
            )
        )

        st.session_state["dialogue"] = dialogue

        st.session_state["audio"] = audio_bytes

        st.session_state["model"] = used_model

        st.session_state["url"] = url

    except Exception as e:

        progress.empty()

        status.empty()

        st.error(
            "❌ Something went wrong."
        )

        st.code(
            str(e)
        )

        st.info(
            "Check your API keys, article URL, "
            "and FFmpeg installation."
        )


# ============================================================
# RESULTS
# ============================================================

if "audio" in st.session_state:

    st.divider()

    st.subheader(
        "🎉 Podcast Ready"
    )

    col1, col2, col3 = st.columns(3)

    # --------------------------------------------------------
    # METRIC 1
    # --------------------------------------------------------

    with col1:

        st.metric(
            "Dialogue Turns",
            len(
                st.session_state[
                    "dialogue"
                ]
            ),
        )

    # --------------------------------------------------------
    # METRIC 2
    # --------------------------------------------------------

    with col2:

        total_chars = sum(
            len(x["text"])
            for x in st.session_state[
                "dialogue"
            ]
        )

        st.metric(
            "Script Characters",
            total_chars,
        )

    # --------------------------------------------------------
    # METRIC 3
    # --------------------------------------------------------

    with col3:

        st.metric(
            "AI Model",
            st.session_state[
                "model"
            ].split("/")[-1][:20],
        )

    # ========================================================
    # TABS
    # ========================================================

    tab1, tab2, tab3 = st.tabs(
        [
            "🎙️ Podcast",
            "🧠 AI Analysis",
            "📄 Article",
        ]
    )

    # ========================================================
    # PODCAST TAB
    # ========================================================

    with tab1:

        st.audio(
            st.session_state[
                "audio"
            ],
            format="audio/mp3",
        )

        st.download_button(
            label="⬇️ Download Podcast MP3",
            data=st.session_state[
                "audio"
            ],
            file_name="blog_podcast.mp3",
            mime="audio/mpeg",
            use_container_width=True,
        )

        st.subheader(
            "💬 Conversation"
        )

        for item in st.session_state[
            "dialogue"
        ]:

            speaker = item[
                "speaker"
            ]

            text = item[
                "text"
            ]

            css_class = (
                "speaker-alex"
                if speaker == "Alex"
                else "speaker-sam"
            )

            st.markdown(
                f"""
                <div class="{css_class}">

                    {speaker}                 

                    {text}

                </div>
                """,
                unsafe_allow_html=True,
            )

    # ========================================================
    # ANALYSIS TAB
    # ========================================================

    with tab2:

        st.markdown(
            '<div class="card">',
            unsafe_allow_html=True,
        )

        st.write(
            st.session_state[
                "analysis"
            ]
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

        st.caption(
            "Generated by OpenRouter."
        )

    # ========================================================
    # ARTICLE TAB
    # ========================================================

    with tab3:

        st.caption(
            st.session_state[
                "url"
            ]
        )

        st.text_area(
            "Extracted Article",
            st.session_state[
                "article"
            ],
            height=500,
        )
