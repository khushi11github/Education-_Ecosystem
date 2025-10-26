// Text-to-Speech Functionality for Visually Impaired Students
// Uses Web Speech API

class TextToSpeech {
    constructor() {
        this.synth = window.speechSynthesis;
        this.utterance = null;
        this.isEnabled = false;
        this.isSpeaking = false;
        this.voices = [];
        
        // Load voices
        this.loadVoices();
        if (speechSynthesis.onvoiceschanged !== undefined) {
            speechSynthesis.onvoiceschanged = () => this.loadVoices();
        }
        
        // Check if user has visual impairment
        this.checkUserSettings();
        
        // Initialize controls
        this.initControls();
    }
    
    loadVoices() {
        this.voices = this.synth.getVoices();
    }
    
    checkUserSettings() {
        // Check if user has visual impairment disability type
        const bodyElement = document.body;
        const disabilityType = bodyElement.getAttribute('data-disability-type');
        
        if (disabilityType === 'visual') {
            this.isEnabled = true;
            this.showTTSControls();
        }
    }
    
    initControls() {
        // Create floating TTS control panel
        const controlPanel = document.createElement('div');
        controlPanel.id = 'tts-controls';
        controlPanel.className = 'tts-control-panel';
        controlPanel.innerHTML = `
            <button id="tts-toggle" class="btn btn-primary btn-sm" title="Toggle Text-to-Speech">
                <i class="bi bi-volume-up"></i> Read Aloud
            </button>
            <button id="tts-stop" class="btn btn-danger btn-sm d-none" title="Stop Reading">
                <i class="bi bi-stop-circle"></i> Stop
            </button>
            <button id="tts-pause" class="btn btn-warning btn-sm d-none" title="Pause">
                <i class="bi bi-pause-circle"></i> Pause
            </button>
            <button id="tts-resume" class="btn btn-success btn-sm d-none" title="Resume">
                <i class="bi bi-play-circle"></i> Resume
            </button>
        `;
        
        document.body.appendChild(controlPanel);
        
        // Add event listeners
        this.attachEventListeners();
    }
    
    showTTSControls() {
        const controls = document.getElementById('tts-controls');
        if (controls) {
            controls.style.display = 'block';
        }
    }
    
    attachEventListeners() {
        // Read on click
        document.getElementById('tts-toggle')?.addEventListener('click', () => {
            this.readPageContent();
        });
        
        document.getElementById('tts-stop')?.addEventListener('click', () => {
            this.stop();
        });
        
        document.getElementById('tts-pause')?.addEventListener('click', () => {
            this.pause();
        });
        
        document.getElementById('tts-resume')?.addEventListener('click', () => {
            this.resume();
        });
        
        // Read on hover for important elements (optional)
        this.addHoverListeners();
    }
    
    addHoverListeners() {
        // Add hover-to-read for headings, buttons, and links
        const elements = document.querySelectorAll('h1, h2, h3, h4, h5, button, a.btn');
        elements.forEach(element => {
            element.addEventListener('mouseenter', (e) => {
                if (this.isEnabled && !this.isSpeaking) {
                    const text = e.target.innerText || e.target.textContent;
                    if (text && text.trim()) {
                        this.speak(text.trim());
                    }
                }
            });
        });
    }
    
    readPageContent() {
        // Get main content area
        const mainContent = document.querySelector('main') || document.body;
        
        // Extract readable text
        let text = this.extractReadableText(mainContent);
        
        if (text) {
            this.speak(text);
            this.updateControlButtons(true);
        }
    }
    
    extractReadableText(element) {
        // Clone the element to avoid modifying the original
        const clone = element.cloneNode(true);
        
        // Remove script and style elements
        const unwanted = clone.querySelectorAll('script, style, nav, footer');
        unwanted.forEach(el => el.remove());
        
        // Get text content
        let text = clone.textContent || clone.innerText;
        
        // Clean up whitespace
        text = text.replace(/\s+/g, ' ').trim();
        
        return text;
    }
    
    speak(text, options = {}) {
        if (!this.synth) {
            console.error('Speech synthesis not supported');
            return;
        }
        
        // Cancel any ongoing speech
        this.synth.cancel();
        
        this.utterance = new SpeechSynthesisUtterance(text);
        
        // Set voice properties
        this.utterance.rate = options.rate || 1.0;  // Speed (0.1 to 10)
        this.utterance.pitch = options.pitch || 1.0; // Pitch (0 to 2)
        this.utterance.volume = options.volume || 1.0; // Volume (0 to 1)
        
        // Use English voice if available
        const englishVoice = this.voices.find(voice => voice.lang === 'en-US' || voice.lang === 'en-GB');
        if (englishVoice) {
            this.utterance.voice = englishVoice;
        }
        
        // Event handlers
        this.utterance.onstart = () => {
            this.isSpeaking = true;
            console.log('Speech started');
        };
        
        this.utterance.onend = () => {
            this.isSpeaking = false;
            this.updateControlButtons(false);
            console.log('Speech ended');
        };
        
        this.utterance.onerror = (event) => {
            console.error('Speech error:', event);
            this.isSpeaking = false;
            this.updateControlButtons(false);
        };
        
        // Speak
        this.synth.speak(this.utterance);
    }
    
    stop() {
        if (this.synth) {
            this.synth.cancel();
            this.isSpeaking = false;
            this.updateControlButtons(false);
        }
    }
    
    pause() {
        if (this.synth && this.isSpeaking) {
            this.synth.pause();
            document.getElementById('tts-pause')?.classList.add('d-none');
            document.getElementById('tts-resume')?.classList.remove('d-none');
        }
    }
    
    resume() {
        if (this.synth) {
            this.synth.resume();
            document.getElementById('tts-pause')?.classList.remove('d-none');
            document.getElementById('tts-resume')?.classList.add('d-none');
        }
    }
    
    updateControlButtons(isSpeaking) {
        const toggleBtn = document.getElementById('tts-toggle');
        const stopBtn = document.getElementById('tts-stop');
        const pauseBtn = document.getElementById('tts-pause');
        const resumeBtn = document.getElementById('tts-resume');
        
        if (isSpeaking) {
            toggleBtn?.classList.add('d-none');
            stopBtn?.classList.remove('d-none');
            pauseBtn?.classList.remove('d-none');
        } else {
            toggleBtn?.classList.remove('d-none');
            stopBtn?.classList.add('d-none');
            pauseBtn?.classList.add('d-none');
            resumeBtn?.classList.add('d-none');
        }
    }
}

// Initialize TTS when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if speech synthesis is supported
    if ('speechSynthesis' in window) {
        window.tts = new TextToSpeech();
    } else {
        console.warn('Text-to-Speech not supported in this browser');
    }
});

// Keyboard shortcut: Ctrl+Shift+R to read page
document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.shiftKey && e.key === 'R') {
        e.preventDefault();
        if (window.tts) {
            window.tts.readPageContent();
        }
    }
    
    // Ctrl+Shift+S to stop
    if (e.ctrlKey && e.shiftKey && e.key === 'S') {
        e.preventDefault();
        if (window.tts) {
            window.tts.stop();
        }
    }
});
