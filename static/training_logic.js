// Theme Toggle
const themeToggle = document.getElementById('theme-toggle');
const html = document.documentElement;

const savedTheme = localStorage.getItem('theme');
const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
const currentTheme = savedTheme || systemTheme;

html.setAttribute('data-theme', currentTheme);
themeToggle.textContent = currentTheme === 'dark' ? '☀️' : '🌙';

themeToggle.addEventListener('click', () => {
    const current = html.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    themeToggle.textContent = next === 'dark' ? '☀️' : '🌙';
    
    if (quizEmicicloIframe.contentWindow) {
        quizEmicicloIframe.contentWindow.postMessage({ type: 'setTheme', theme: next }, '*');
    }
    if (emicicloViewIframe.contentWindow) {
        emicicloViewIframe.contentWindow.postMessage({ type: 'setTheme', theme: next }, '*');
    }
});

// Game Logic
document.addEventListener('DOMContentLoaded', () => {
    // Screen elements
    const setupScreen = document.getElementById('setup-screen');
    const gameScreen = document.getElementById('game-screen');
    const manualGameScreen = document.getElementById('manual-game-screen');
    const seatGameScreen = document.getElementById('seat-game-screen');
    const clickSeatGameScreen = document.getElementById('click-seat-game-screen');
    const endScreen = document.getElementById('end-screen');
    const searchScreen = document.getElementById('search-screen');
    const selectionScreen = document.getElementById('selection-screen');
    const modalOverlay = document.getElementById('modal-overlay'); 

    // Setup elements
    const gameModeSelect = document.getElementById('game-mode-select');
    const deputySourceSelect = document.getElementById('deputy-source-select');
    const manualSelectionControls = document.getElementById('manual-selection-controls');
    const openSelectionModalBtn = document.getElementById('open-selection-modal-btn');
    const selectedCountInfo = document.getElementById('selected-count-info');
    const groupSelectContainer = document.getElementById('group-select-container');
    const roundsInputContainer = document.getElementById('rounds-input-container');
    const groupSelect = document.getElementById('group-select');
    const roundsInput = document.getElementById('rounds-input');
    const startBtn = document.getElementById('start-btn');
    const deputyCountInfo = document.getElementById('deputy-count-info');
    const searchBtn = document.getElementById('search-btn'); 

    // Game elements (Classic)
    const progressText = document.getElementById('progress-text');
    const scoreText = document.getElementById('score-text');
    const deputyImage = document.getElementById('deputy-image');
    const answersContainer = document.getElementById('answers-container');
    const feedbackText = document.getElementById('feedback-text');
    const quitBtn = document.getElementById('quit-btn');
    
    // Game elements (Manual)
    const manualProgressText = document.getElementById('manual-progress-text');
    const manualScoreText = document.getElementById('manual-score-text');
    const manualDeputyImage = document.getElementById('manual-deputy-image');
    const lastnameInput = document.getElementById('lastname-input');
    const groupGuessWrapper = document.getElementById('group-guess-wrapper');
    const groupGuessSelect = document.getElementById('group-guess-select');
    const hintGroupBtn = document.getElementById('hint-group-btn');
    const hintInitialBtn = document.getElementById('hint-initial-btn');
    const hintsDisplayArea = document.getElementById('hints-display-area');
    const submitManualAnswerBtn = document.getElementById('submit-manual-answer-btn');
    const manualFeedbackText = document.getElementById('manual-feedback-text');
    const manualQuitBtn = document.getElementById('manual-quit-btn');
    
    // Game elements (Seat)
    const seatProgressText = document.getElementById('seat-progress-text');
    const seatScoreText = document.getElementById('seat-score-text');
    const seatDeputyImage = document.getElementById('seat-deputy-image');
    const seatInput = document.getElementById('seat-input');
    const submitSeatAnswerBtn = document.getElementById('submit-seat-answer-btn');
    const seatFeedbackText = document.getElementById('seat-feedback-text');
    const seatQuitBtn = document.getElementById('seat-quit-btn');
    
    // Game elements (Click-Seat)
    const clickSeatProgressText = document.getElementById('click-seat-progress-text');
    const clickSeatScoreText = document.getElementById('click-seat-score-text');
    const clickSeatQuestionText = document.getElementById('click-seat-question-text');
    const quizEmicicloIframe = document.getElementById('quiz-emiciclo-iframe');
    const clickSeatFeedbackText = document.getElementById('click-seat-feedback-text');
    const clickSeatQuitBtn = document.getElementById('click-seat-quit-btn');

    // End screen elements
    const finalScoreText = document.getElementById('final-score-text');
    const resultsSummaryContainer = document.getElementById('results-summary-container');
    const restartBtn = document.getElementById('restart-btn');
    
    // Search elements
    const searchBackBtn = document.getElementById('search-back-btn');
    const searchCognomeInput = document.getElementById('search-cognome-input');
    const searchNomeInput = document.getElementById('search-nome-input');
    const searchGruppoSelect = document.getElementById('search-gruppo-select');
    const searchCommitteeSelect = document.getElementById('search-committee-select');
    const searchResultsContainer = document.getElementById('search-results-container');
    const searchShowCessati = document.getElementById('search-show-cessati'); // NUOVO
    
    // Selection Screen elements
    const selectionCounter = document.getElementById('selection-counter');
    const selectionDoneBtn = document.getElementById('selection-done-btn');
    const selectCognomeInput = document.getElementById('select-cognome-input');
    const selectNomeInput = document.getElementById('select-nome-input');
    const selectGruppoSelect = document.getElementById('select-gruppo-select');
    const selectCommitteeSelect = document.getElementById('select-committee-select');
    const selectionResultsContainer = document.getElementById('selection-results-container');
    const selectionSelectAllVisibleBtn = document.getElementById('selection-select-all-visible-btn');
    const selectionDeselectAllVisibleBtn = document.getElementById('selection-deselect-all-visible-btn');
    const selectShowCessati = document.getElementById('select-show-cessati'); // NUOVO

    
    // Modal elements
    const modalContent = document.getElementById('modal-content');
    const modalCloseBtn = document.getElementById('modal-close-btn');
    const modalImage = document.getElementById('modal-image');
    const modalName = document.getElementById('modal-name');
    const modalGroup = document.getElementById('modal-group');
    const modalConstituency = document.getElementById('modal-constituency');
    const modalGender = document.getElementById('modal-gender');
    const modalSeat = document.getElementById('modal-seat');
    const modalEmiciclo = document.getElementById('modal-emiciclo');
    const modalCommitteesContainer = document.getElementById('modal-committees-container');
    const modalCommittees = document.getElementById('modal-committees');
    
    // Elementi Modale Emiciclo
    const viewEmicicloBtn = document.getElementById('view-emiciclo-btn');
    const emicicloViewOverlay = document.getElementById('emiciclo-view-overlay');
    const emicicloViewCloseBtn = document.getElementById('emiciclo-view-close-btn');
    const emicicloViewIframe = document.getElementById('emiciclo-view-iframe');

    // NUOVI ELEMENTI AUDIO
    const audioCorrect = document.getElementById('audio-correct');
    const audioIncorrect = document.getElementById('audio-incorrect');
    const audioStart = document.getElementById('audio-start');

    // Game state variables
    let allDeputies = [];
    let allGroups = []; 
    let allGroupsNoTutti = []; 
    let sessionDeputies = [];
    let sessionResults = [];
    let customDeputyList = [];
    let currentQuestionIndex = 0;
    let score = 0;
    let totalRounds = 10;
    let correctDeputy = null;
    let nextQuestionTimeout = null;
    let currentGameMode = 'classic';
    let sessionGroupFilter = 'Tutti';
    let iframeReady = false;

    async function initialize() {
        const [deputiesRes, groupsRes, committeesRes] = await Promise.all([
            fetch('/api/deputies'),
            fetch('/api/groups'),
            fetch('/api/committees')
        ]);
        allDeputies = await deputiesRes.json();
        allGroups = await groupsRes.json(); 
        const committees = await committeesRes.json();
        
        allGroupsNoTutti = allGroups.filter(g => g !== 'Tutti'); 

        const groupOptionsHTML = allGroups.map(g => `<option value="${g}">${g}</option>`).join('');
        groupSelect.innerHTML = groupOptionsHTML;
        searchGruppoSelect.innerHTML = groupOptionsHTML;
        selectGruppoSelect.innerHTML = groupOptionsHTML;
        
        groupGuessSelect.innerHTML = `<option value="">Seleziona un gruppo...</option>` +
            allGroupsNoTutti.map(g => `<option value="${g}">${g}</option>`).join('');
        
        const committeeOptionsHTML = committees.map(c => `<option value="${c}">${c}</option>`).join('');
        searchCommitteeSelect.innerHTML = committeeOptionsHTML;
        selectCommitteeSelect.innerHTML = committeeOptionsHTML;
        
        updateDeputyCount();
        groupSelect.addEventListener('change', updateDeputyCount);
        
        renderSearchResults();
        
        deputySourceSelect.addEventListener('change', toggleDeputySourceControls);
        openSelectionModalBtn.addEventListener('click', showSelectionScreen);
        selectionDoneBtn.addEventListener('click', hideSelectionScreen);
        
        selectCognomeInput.addEventListener('input', renderSelectionList);
        selectNomeInput.addEventListener('input', renderSelectionList);
        selectGruppoSelect.addEventListener('change', renderSelectionList);
        selectCommitteeSelect.addEventListener('change', renderSelectionList);
        selectShowCessati.addEventListener('input', renderSelectionList); // NUOVO
        
        selectionSelectAllVisibleBtn.addEventListener('click', selectAllVisible);
        selectionDeselectAllVisibleBtn.addEventListener('click', deselectAllVisible);
    }

    function updateDeputyCount() {
        const selectedGroup = groupSelect.value;
        let availableCount = 0;
        
        const currentMode = gameModeSelect.value;
        
        let availableDeputies = (selectedGroup === 'Tutti')
            ? allDeputies
            : allDeputies.filter(d => d.simple_group === selectedGroup);
        
        // --- MODIFICA: Filtra i cessati anche dal conteggio ---
        availableDeputies = availableDeputies.filter(d => d.status !== 'cessato');
        
        if (currentMode === 'seat' || currentMode === 'click-seat') {
            availableCount = availableDeputies.filter(d => d.seat && d.seat !== 'N/D').length;
        } else {
            availableCount = availableDeputies.length;
        }
        
        deputyCountInfo.textContent = `${availableCount} deputati disponibili (in carica) in questo gruppo`;
    }
    
    gameModeSelect.addEventListener('change', updateDeputyCount);

    function toggleDeputySourceControls() {
        const source = deputySourceSelect.value;
        if (source === 'manual') {
            groupSelectContainer.classList.add('hidden');
            roundsInputContainer.classList.add('hidden');
            manualSelectionControls.classList.remove('hidden');
            deputyCountInfo.classList.add('hidden');
        } else {
            groupSelectContainer.classList.remove('hidden');
            roundsInputContainer.classList.remove('hidden');
            manualSelectionControls.classList.add('hidden');
            deputyCountInfo.classList.remove('hidden');
            updateDeputyCount();
        }
    }
    
    function showSelectionScreen() {
        setupScreen.classList.add('hidden');
        selectionScreen.classList.remove('hidden');
        renderSelectionList();
        updateSelectionCounter();
    }

    function hideSelectionScreen() {
        selectionScreen.classList.add('hidden');
        setupScreen.classList.remove('hidden');
        selectedCountInfo.textContent = `${customDeputyList.length} deputati selezionati`;
    }

    function renderSelectionList() {
        const cognomeFilter = selectCognomeInput.value.toLowerCase().trim();
        const nomeFilter = selectNomeInput.value.toLowerCase().trim();
        const gruppoFilter = selectGruppoSelect.value;
        const committeeFilter = selectCommitteeSelect.value;
        const showCessati = selectShowCessati.checked; // NUOVO
        
        selectionResultsContainer.innerHTML = ''; 
        
        const filteredDeputies = allDeputies.filter(deputy => {
            const nameParts = deputy.name.toLowerCase().split('(')[0].trim().split(' ');
            const cognome = nameParts[0];
            const nome = nameParts.slice(1).join(' ');
            
            const matchCognome = cognome.startsWith(cognomeFilter);
            const matchNome = nome.startsWith(nomeFilter);
            const matchGruppo = (gruppoFilter === 'Tutti') || (deputy.simple_group === gruppoFilter);
            const matchCommittee = (committeeFilter === 'Tutte') || (deputy.committees.includes(committeeFilter));
            const matchStatus = showCessati || deputy.status !== 'cessato'; // NUOVO
            
            return matchCognome && matchNome && matchGruppo && matchCommittee && matchStatus; // MODIFICATO
        });
        
        if (filteredDeputies.length === 0) {
            selectionResultsContainer.innerHTML = `<p id="no-results-text">Nessun deputato trovato.</p>`;
            return;
        }
        
        filteredDeputies.forEach(deputy => {
            const item = document.createElement('div');
            item.className = 'selection-result-item';
            
            item.setAttribute('data-deputy-name', deputy.name); 
            
            const isSelected = customDeputyList.some(d => d.name === deputy.name);
            if (isSelected) {
                item.classList.add('selected');
            }
            
            // --- MODIFICA: Aggiungi tag (Cessato) ---
            const statusTag = deputy.status === 'cessato' ? ' <span class="status-tag">(Cessato)</span>' : '';
            
            item.innerHTML = `
                <img src="${deputy.photo_url}" class="result-thumb" alt="${deputy.name}">
                <div class="result-info">
                    <div class="name">${deputy.name}${statusTag}</div>
                    <div class="group">${deputy.group}</div>
                </div>
            `;
            item.addEventListener('click', () => toggleDeputySelection(deputy, item));
            selectionResultsContainer.appendChild(item);
        });
    }

    function toggleDeputySelection(deputy, itemElement) {
        const index = customDeputyList.findIndex(d => d.name === deputy.name);
        if (index > -1) {
            customDeputyList.splice(index, 1);
            itemElement.classList.remove('selected');
        } else {
            customDeputyList.push(deputy);
            itemElement.classList.add('selected');
        }
        updateSelectionCounter();
    }

     function updateSelectionCounter() {
        selectionCounter.textContent = `Selezionati: ${customDeputyList.length}`;
     }
     
    function selectAllVisible() {
        const visibleItems = selectionResultsContainer.querySelectorAll('.selection-result-item');
        
        visibleItems.forEach(item => {
            const deputyName = item.getAttribute('data-deputy-name');
            const deputy = allDeputies.find(d => d.name === deputyName);
            if (!deputy) return;

            const isSelected = customDeputyList.some(d => d.name === deputy.name);
            if (!isSelected) {
                customDeputyList.push(deputy);
            }
            item.classList.add('selected');
        });
        updateSelectionCounter();
    }

    function deselectAllVisible() {
        const visibleItems = selectionResultsContainer.querySelectorAll('.selection-result-item');
        
        visibleItems.forEach(item => {
            const deputyName = item.getAttribute('data-deputy-name');
            const index = customDeputyList.findIndex(d => d.name === deputyName);

            if (index > -1) {
                customDeputyList.splice(index, 1);
            }
            item.classList.remove('selected');
        });
        updateSelectionCounter();
    }

    function startTraining() {
        // NUOVO: Suono avvio
        audioStart.play().catch(e => console.warn("La riproduzione audio è stata bloccata dal browser."));
        
        currentGameMode = gameModeSelect.value;
        const source = deputySourceSelect.value;
        let availableDeputies = [];

        if (source === 'manual') {
            if (customDeputyList.length === 0) {
                alert("Non hai selezionato nessun deputato per l'allenamento!");
                return;
            }
            // --- MODIFICA: Filtra i cessati anche dalla lista custom ---
            availableDeputies = customDeputyList.filter(d => d.status !== 'cessato');
            
            if (availableDeputies.length === 0) {
                 alert("Tutti i deputati selezionati sono cessati dal mandato e non possono essere usati nel quiz.");
                 return;
            }

        } else {
            sessionGroupFilter = groupSelect.value;
            totalRounds = parseInt(roundsInput.value, 10);
            
            let filteredByGroup = (sessionGroupFilter === 'Tutti')
                ? [...allDeputies]
                : allDeputies.filter(d => d.simple_group === sessionGroupFilter);
            
            // --- MODIFICA: Filtra i cessati ---
            availableDeputies = filteredByGroup.filter(d => d.status !== 'cessato');
        }
        
        if (currentGameMode === 'seat' || currentGameMode === 'click-seat') {
            availableDeputies = availableDeputies.filter(d => d.seat && d.seat !== 'N/D');
            if (availableDeputies.length === 0) {
                const msg = source === 'manual' 
                    ? "Nessuno dei deputati selezionati (in carica) ha un seggio valido per questa modalità."
                    : "Non ci sono deputati (in carica) con un seggio assegnato in questo gruppo per questa modalità.";
                alert(msg);
                return;
            }
        } else if (currentGameMode === 'classic' && availableDeputies.length < 4) {
             const msg = source === 'manual'
                ? "Devi selezionare almeno 4 deputati (in carica) per la modalità Classica."
                : "Questo gruppo non ha abbastanza deputati (in carica, minimo 4) per iniziare l'allenamento.";
            alert(msg);
            return;
        } else if (availableDeputies.length === 0 && source !== 'manual') {
            alert("Nessun deputato (in carica) disponibile per questo gruppo.");
            return;
        }

        shuffleArray(availableDeputies);
        
        if (source === 'all') {
            sessionDeputies = availableDeputies.slice(0, Math.min(totalRounds, availableDeputies.length));
        } else {
             sessionDeputies = availableDeputies;
        }
        totalRounds = sessionDeputies.length;

        currentQuestionIndex = 0;
        score = 0;
        sessionResults = [];
        
        setupScreen.classList.add('hidden');
        endScreen.classList.add('hidden');
        
        if (currentGameMode === 'classic') {
            gameScreen.classList.remove('hidden');
            displayNextQuestion();
        } else if (currentGameMode === 'manual') {
            manualGameScreen.classList.remove('hidden');
            displayNextManualQuestion();
        } else if (currentGameMode === 'seat') {
            seatGameScreen.classList.remove('hidden');
            displayNextSeatQuestion();
        } else if (currentGameMode === 'click-seat') {
            clickSeatGameScreen.classList.remove('hidden');
            const currentTheme = html.getAttribute('data-theme') || 'light';
            // NUOVO CODICE: Usa emiciclo_universale in modalità quiz
            quizEmicicloIframe.src = `/emiciclo?mode=quiz&theme=${currentTheme}`;
        }
    }
    
    function displayNextQuestion() {
        if (currentQuestionIndex >= totalRounds) {
            endSession();
            return;
        }
        updateGameHeader();
        feedbackText.textContent = '';
        feedbackText.className = 'feedback-text';
        
        correctDeputy = sessionDeputies[currentQuestionIndex];
        deputyImage.src = correctDeputy.photo_url;
        
        const correctGender = correctDeputy.gender;
        let wrongOptionsPool;
        
        // --- MODIFICA: Assicurati che il pool di opzioni sbagliate sia solo tra quelli in carica ---
        let sourcePool = (deputySourceSelect.value === 'manual' && customDeputyList.length >= 4)
            ? customDeputyList.filter(d => d.status !== 'cessato')
            : allDeputies.filter(d => d.status !== 'cessato');
        
        if (sessionGroupFilter === 'Tutti' || deputySourceSelect.value === 'manual') {
            wrongOptionsPool = sourcePool.filter(d => 
                d.name !== correctDeputy.name && 
                d.gender === correctGender
            );
        } else {
            wrongOptionsPool = sourcePool.filter(d => 
                d.name !== correctDeputy.name && 
                d.gender === correctGender &&
                d.simple_group === sessionGroupFilter
            );
        }

        shuffleArray(wrongOptionsPool);
        let wrongOptions = wrongOptionsPool.slice(0, 3);

        if (wrongOptions.length < 3) {
            let needed = 3 - wrongOptions.length;
            const existingNames = [correctDeputy.name, ...wrongOptions.map(d => d.name)];
            // Fallback pool (sempre filtrato per 'in carica')
            let fallbackPool1 = allDeputies.filter(d => 
                d.status !== 'cessato' &&
                !existingNames.includes(d.name) &&
                d.gender === correctGender
            );
            shuffleArray(fallbackPool1);
            wrongOptions = [...wrongOptions, ...fallbackPool1.slice(0, needed)];
        }
        
        if (wrongOptions.length < 3) {
             let needed = 3 - wrongOptions.length;
             const existingNames = [correctDeputy.name, ...wrongOptions.map(d => d.name)];
             let fallbackPool2 = allDeputies.filter(d => d.status !== 'cessato' && !existingNames.includes(d.name));
             shuffleArray(fallbackPool2);
             wrongOptions = [...wrongOptions, ...fallbackPool2.slice(0, needed)];
        }

        const options = [correctDeputy, ...wrongOptions];
        shuffleArray(options);
        
        answersContainer.innerHTML = '';
        options.forEach(option => {
            const button = document.createElement('button');
            button.className = 'answer-btn';
            button.innerHTML = `<span class="name">${option.name}</span><span class="group">${option.group}</span>`;
            button.onclick = () => handleAnswer(option.name === correctDeputy.name, button);
            answersContainer.appendChild(button);
        });
    }

    function handleAnswer(isCorrect, clickedButton) {
        document.querySelectorAll('.answer-btn').forEach(btn => btn.disabled = true);
        
        sessionResults.push({ deputy: correctDeputy, correct: isCorrect });
        
        if (isCorrect) {
            score++;
            clickedButton.classList.add('correct');
            feedbackText.textContent = '✓ Corretto!';
            feedbackText.className = 'feedback-text correct';
            audioCorrect.play().catch(e => console.warn("Audio play failed")); // NUOVO
        } else {
            clickedButton.classList.add('incorrect');
            feedbackText.textContent = `✗ Sbagliato! La risposta era ${correctDeputy.name}`;
            feedbackText.className = 'feedback-text incorrect';
            audioIncorrect.play().catch(e => console.warn("Audio play failed")); // NUOVO
            document.querySelectorAll('.answer-btn').forEach(btn => {
                if (btn.querySelector('.name').textContent === correctDeputy.name) {
                    btn.classList.add('correct');
                }
            });
        }
        updateGameHeader();
        currentQuestionIndex++;
        nextQuestionTimeout = setTimeout(displayNextQuestion, 2000);
    }
    
    
    function displayNextManualQuestion() {
        if (currentQuestionIndex >= totalRounds) {
            endSession();
            return;
        }
        updateGameHeader();
        correctDeputy = sessionDeputies[currentQuestionIndex];
        manualDeputyImage.src = correctDeputy.photo_url;
        lastnameInput.value = '';
        manualFeedbackText.textContent = '';
        manualFeedbackText.className = 'feedback-text';
        hintsDisplayArea.innerHTML = '';
        hintsDisplayArea.classList.add('hidden');
        
        if (sessionGroupFilter === 'Tutti' || deputySourceSelect.value === 'manual') {
            groupGuessWrapper.classList.remove('hidden');
            groupGuessSelect.value = ''; 
        } else {
            groupGuessWrapper.classList.add('hidden');
            groupGuessSelect.value = sessionGroupFilter; 
        }
        submitManualAnswerBtn.disabled = false;
        lastnameInput.disabled = false;
        groupGuessSelect.disabled = false;
        hintGroupBtn.disabled = false;
        hintInitialBtn.disabled = false;
        lastnameInput.focus();
    }
    
    function handleManualAnswer() {
        lastnameInput.blur();
        const guessName = lastnameInput.value.trim();
        const guessGroup = groupGuessSelect.value;
        const correctGroup = correctDeputy.simple_group;
        const normalize = (str) => str.normalize('NFD')
                                  .replace(/[\u0300-\u036f]/g, "") 
                                  .toLowerCase()
                                  .replace(/[^a-z0-9]/g, ' '); 
        
        const normalizedGuessName = normalize(guessName);
        const normalizedCorrectName = normalize(correctDeputy.name.split('(')[0]);
        
        const isNameCorrect = normalizedGuessName.length > 2 && normalizedCorrectName.includes(normalizedGuessName);
        const isGroupCorrect = guessGroup === correctGroup;
        const fullAnswer = `${correctDeputy.name} (${correctDeputy.group})`;
        
        let roundCorrect = false;
        if (sessionGroupFilter !== 'Tutti' && deputySourceSelect.value !== 'manual') {
            if (isNameCorrect) roundCorrect = true;
        } else {
            if (isNameCorrect && isGroupCorrect) roundCorrect = true;
        }
        
        sessionResults.push({ deputy: correctDeputy, correct: roundCorrect });
        
        submitManualAnswerBtn.disabled = true;
        lastnameInput.disabled = true;
        groupGuessSelect.disabled = true;
        hintGroupBtn.disabled = true;
        hintInitialBtn.disabled = true;
        
        if (roundCorrect) {
            score++;
            manualFeedbackText.textContent = `✓ Corretto! Era ${fullAnswer}`;
            manualFeedbackText.className = 'feedback-text correct';
            audioCorrect.play().catch(e => console.warn("Audio play failed")); // NUOVO
        } else {
            manualFeedbackText.textContent = `✗ Sbagliato! La risposta corretta era ${fullAnswer}`;
            manualFeedbackText.className = 'feedback-text incorrect';
            audioIncorrect.play().catch(e => console.warn("Audio play failed")); // NUOVO
        }
        updateGameHeader();
        currentQuestionIndex++;
        nextQuestionTimeout = setTimeout(displayNextManualQuestion, 2500);
    }
    
    function handleHintGroup() {
        hintsDisplayArea.innerHTML = `<p>Gruppo: <strong>${correctDeputy.simple_group}</strong></p>`;
        hintsDisplayArea.classList.remove('hidden');
        hintGroupBtn.disabled = true;
    }
    
    function handleHintInitial() {
        const nameParts = correctDeputy.name.split(' ');
        const lastName = nameParts[0]; 
        const initial = lastName.charAt(0).toUpperCase();
        hintsDisplayArea.innerHTML += `<p>Iniziale Cognome: <strong>${initial}</strong></p>`;
        hintsDisplayArea.classList.remove('hidden');
        hintInitialBtn.disabled = true;
    }
    
    
    function displayNextSeatQuestion() {
        if (currentQuestionIndex >= totalRounds) {
            endSession();
            return;
        }
        updateGameHeader();
        correctDeputy = sessionDeputies[currentQuestionIndex];
        
        seatDeputyImage.src = correctDeputy.photo_url;
        seatInput.value = '';
        seatFeedbackText.textContent = '';
        seatFeedbackText.className = 'feedback-text';
        submitSeatAnswerBtn.disabled = false;
        seatInput.disabled = false;
        seatInput.focus();
    }
    
    function handleSeatAnswer() {
        const guessSeat = seatInput.value.trim();
        const correctSeat = correctDeputy.seat;
        const isCorrect = (guessSeat === correctSeat);

        sessionResults.push({ deputy: correctDeputy, correct: isCorrect });
        
        submitSeatAnswerBtn.disabled = true;
        seatInput.disabled = true;

        if (isCorrect) {
            score++;
            seatFeedbackText.textContent = `✓ Corretto! È il seggio ${correctSeat}.`;
            seatFeedbackText.className = 'feedback-text correct';
            audioCorrect.play().catch(e => console.warn("Audio play failed")); // NUOVO
        } else {
            seatFeedbackText.textContent = `✗ Sbagliato! Era ${correctDeputy.name}, seggio ${correctSeat}.`;
            seatFeedbackText.className = 'feedback-text incorrect';
            audioIncorrect.play().catch(e => console.warn("Audio play failed")); // NUOVO
        }
        updateGameHeader();
        currentQuestionIndex++;
        nextQuestionTimeout = setTimeout(displayNextSeatQuestion, 2500);
    }
    
    function quitSeatGame() {
         if (nextQuestionTimeout) clearTimeout(nextQuestionTimeout);
        seatGameScreen.classList.add('hidden');
        setupScreen.classList.remove('hidden');
    }
    
    
    function displayNextClickSeatQuestion() {
        if (!iframeReady) return;
        if (currentQuestionIndex >= totalRounds) {
            endSession();
            return;
        }
        updateGameHeader();
        correctDeputy = sessionDeputies[currentQuestionIndex];
        
        clickSeatQuestionText.innerHTML = `Dove siede <strong>${correctDeputy.name}</strong>?`;
        clickSeatFeedbackText.textContent = '';
        clickSeatFeedbackText.className = 'feedback-text';

        if (quizEmicicloIframe.contentWindow) {
            quizEmicicloIframe.contentWindow.postMessage({ type: 'reset' }, '*');
        }
    }
    
    function handleIframeAnswer(guessedSeat) {
        const correctSeat = correctDeputy.seat;
        const isCorrect = (guessedSeat === correctSeat);

        sessionResults.push({ deputy: correctDeputy, correct: isCorrect });
        
        if (quizEmicicloIframe.contentWindow) {
            quizEmicicloIframe.contentWindow.postMessage({ 
                type: 'showAnswer', 
                correct: correctSeat, 
                guessed: guessedSeat 
            }, '*');
        }

        if (isCorrect) {
            score++;
            clickSeatFeedbackText.textContent = `✓ Corretto! È il seggio ${correctSeat}.`;
            clickSeatFeedbackText.className = 'feedback-text correct';
            audioCorrect.play().catch(e => console.warn("Audio play failed")); // NUOVO
        } else {
            clickSeatFeedbackText.textContent = `✗ Sbagliato! ${correctDeputy.name} siede al ${correctSeat}.`;
            clickSeatFeedbackText.className = 'feedback-text incorrect';
            audioIncorrect.play().catch(e => console.warn("Audio play failed")); // NUOVO
        }
        
        updateGameHeader();
        currentQuestionIndex++;
        nextQuestionTimeout = setTimeout(displayNextClickSeatQuestion, 2500);
    }
    
    function quitClickSeatGame() {
         if (nextQuestionTimeout) clearTimeout(nextQuestionTimeout);
        clickSeatGameScreen.classList.add('hidden');
        quizEmicicloIframe.src = 'about:blank';
        iframeReady = false;
        setupScreen.classList.remove('hidden');
    }
    
    window.addEventListener('message', (event) => {
        const data = event.data;
        
        if (event.source === quizEmicicloIframe.contentWindow) {
            if (data.type === 'seatClick') {
                handleIframeAnswer(data.seat);
            }
            if (data.type === 'iframeReady') {
                iframeReady = true;
                displayNextClickSeatQuestion();
            }
        }
        
       if (event.source === emicicloViewIframe.contentWindow) {
            if (data.type === 'mapSeatClick') {
                const seatNumber = data.seat;
                console.log('Click ricevuto dal seggio:', seatNumber);
                
                // MODIFICA IMPORTANTE: Confronto robusto (converte entrambi in stringa)
                const deputy = allDeputies.find(d => String(d.seat) === String(seatNumber));
                
                if (deputy) {
                    console.log('Deputato trovato:', deputy.name);
                    showDeputyDetails(deputy);
                } else {
                    console.log('Nessun deputato trovato per il seggio', seatNumber);
                    // Opzionale: Mostra un alert se il seggio è vacante
                    // alert('Seggio Vacante');
                }
            }
        }
    });
    
    
    function showSearchScreen() {
        setupScreen.classList.add('hidden');
        searchScreen.classList.remove('hidden');
    }
    
    function hideSearchScreen() {
        searchScreen.classList.add('hidden');
        setupScreen.classList.remove('hidden');
    }
    
    function renderSearchResults() {
        const cognomeFilter = searchCognomeInput.value.toLowerCase().trim();
        const nomeFilter = searchNomeInput.value.toLowerCase().trim();
        const gruppoFilter = searchGruppoSelect.value;
        const committeeFilter = searchCommitteeSelect.value;
        const showCessati = searchShowCessati.checked; // NUOVO
        
        searchResultsContainer.innerHTML = ''; 
        
        const filteredDeputies = allDeputies.filter(deputy => {
            const nameParts = deputy.name.toLowerCase().split('(')[0].trim().split(' ');
            const cognome = nameParts[0];
            const nome = nameParts.slice(1).join(' ');
            
            const matchCognome = cognome.startsWith(cognomeFilter);
            const matchNome = nome.startsWith(nomeFilter);
            const matchGruppo = (gruppoFilter === 'Tutti') || (deputy.simple_group === gruppoFilter);
            const matchCommittee = (committeeFilter === 'Tutte') || (deputy.committees.includes(committeeFilter));
            const matchStatus = showCessati || deputy.status !== 'cessato'; // NUOVO
            
            return matchCognome && matchNome && matchGruppo && matchCommittee && matchStatus; // MODIFICATO
        });
        
        if (filteredDeputies.length === 0) {
            searchResultsContainer.innerHTML = `<p id="no-results-text">Nessun deputato trovato.</p>`;
            return;
        }
        
        filteredDeputies.forEach(deputy => {
            const item = document.createElement('div');
            item.className = 'search-result-item';
            
            // --- MODIFICA: Aggiungi tag (Cessato) ---
            const statusTag = deputy.status === 'cessato' ? ' <span class="status-tag">(Cessato)</span>' : '';
            
            item.innerHTML = `
                <img src="${deputy.photo_url}" class="result-thumb" alt="${deputy.name}">
                <div class="result-info">
                    <div class="name">${deputy.name}${statusTag}</div>
                    <div class="group">${deputy.group}</div>
                </div>
            `;
            item.addEventListener('click', () => showDeputyDetails(deputy));
            searchResultsContainer.appendChild(item);
        });
    }
    
    function showDeputyDetails(deputy) {
        modalImage.src = deputy.photo_url;
        
        // --- MODIFICA: Aggiungi tag (Cessato) al nome nella modale ---
        const statusTag = deputy.status === 'cessato' ? ' <span class="status-tag">(Cessato)</span>' : '';
        modalName.innerHTML = `${deputy.name}${statusTag}`; // Usa innerHTML
        
        modalGroup.textContent = deputy.group;
        
        modalConstituency.textContent = `Circoscrizione: ${deputy.constituency || 'N/D'}`;
        const genderText = deputy.gender === 'male' ? 'Uomo' : (deputy.gender === 'female' ? 'Donna' : 'N/D');
        modalGender.textContent = `Genere: ${genderText}`;
        
       if (deputy.seat && deputy.seat !== 'N/D') {
            modalSeat.textContent = `Seggio n. ${deputy.seat}`;
            modalSeat.classList.remove('hidden');
            
            // NUOVO CODICE: Usa emiciclo_universale in modalità embed
            const currentTheme = html.getAttribute('data-theme') || 'light';
            modalEmiciclo.src = `/emiciclo?mode=embed&highlight=${deputy.seat}&theme=${currentTheme}`;
            modalEmiciclo.classList.remove('hidden');
        } else {
            modalSeat.textContent = 'Seggio: N/D';
            modalSeat.classList.add('hidden'); 
            modalEmiciclo.src = 'about:blank'; 
            modalEmiciclo.classList.add('hidden');
        }
        
        if (deputy.committees && deputy.committees.length > 0) {
            const committeeListHTML = '<ul>' + 
                deputy.committees.map(c => `<li>${c}</li>`).join('') + 
                '</ul>';
            modalCommittees.innerHTML = committeeListHTML;
            modalCommitteesContainer.classList.remove('hidden');
        } else {
            modalCommittees.innerHTML = '';
            modalCommitteesContainer.classList.add('hidden');
        }
        
        modalOverlay.classList.remove('hidden');
    }
    
    function hideModal() {
        modalOverlay.classList.add('hidden');
        modalEmiciclo.src = 'about:blank'; 
    }
    
    
   function showEmicicloMap() {
        const currentTheme = html.getAttribute('data-theme') || 'light';
        // NUOVO CODICE: Usa emiciclo_universale in modalità default
        emicicloViewIframe.src = `/emiciclo?mode=default&theme=${currentTheme}`;
        
        // Nascondi la vecchia legenda HTML statica, perché la nuova mappa ha la sua
        const oldLegend = document.getElementById('emiciclo-view-legend');
        if(oldLegend) oldLegend.style.display = 'none';
        
        emicicloViewOverlay.classList.remove('hidden');
    }
    
    function hideEmicicloMap() {
        emicicloViewOverlay.classList.add('fade-out');
        setTimeout(() => {
            emicicloViewOverlay.classList.add('hidden');
            emicicloViewOverlay.classList.remove('fade-out');
            emicicloViewIframe.src = 'about:blank';
        }, 200); 
    }
    
    
    function endSession() {
        gameScreen.classList.add('hidden');
        manualGameScreen.classList.add('hidden'); 
        seatGameScreen.classList.add('hidden'); 
        clickSeatGameScreen.classList.add('hidden');
        endScreen.classList.remove('hidden');
        finalScoreText.textContent = `${score} / ${totalRounds}`;
        
        renderEndGameSummary();
    }
    
    function renderEndGameSummary() {
        resultsSummaryContainer.innerHTML = '';
        
        if (sessionResults.length === 0) return;
        
        sessionResults.forEach(result => {
            const item = document.createElement('div');
            item.className = 'result-summary-item';

            const nameParts = result.deputy.name.split(' ');
            const lastName = nameParts[0].toUpperCase();
            const firstName = nameParts.slice(1).join(' ');
            const formattedName = `${lastName} ${firstName}`;
            
            const iconClass = result.correct ? 'correct' : 'incorrect';
            const icon = result.correct ? '✓' : '✗';

            item.innerHTML = `
                <img src="${result.deputy.photo_url}" class="result-summary-thumb" alt="${result.deputy.name}">
                <div class="result-summary-info">
                    <div class="name">${formattedName}</div>
                    <div class="group">${result.deputy.group}</div>
                </div>
                <div class="result-summary-icon ${iconClass}">${icon}</div>
            `;
            resultsSummaryContainer.appendChild(item);
        });
    }

    function restartTraining() {
        endScreen.classList.add('hidden');
        setupScreen.classList.remove('hidden');
        toggleDeputySourceControls(); 
    }
    
    function quitGame() {
        if (nextQuestionTimeout) clearTimeout(nextQuestionTimeout);
        gameScreen.classList.add('hidden');
        setupScreen.classList.remove('hidden');
    }
    
    function quitManualGame() {
         if (nextQuestionTimeout) clearTimeout(nextQuestionTimeout);
        manualGameScreen.classList.add('hidden');
        setupScreen.classList.remove('hidden');
    }
    
    function updateGameHeader() {
        const progress = `Domanda ${currentQuestionIndex + 1} / ${totalRounds}`;
        const scoreTextContent = `Punteggio: ${score}`;
        if (currentGameMode === 'classic') {
            progressText.textContent = progress;
            scoreText.textContent = scoreTextContent;
        } else if (currentGameMode === 'manual') {
            manualProgressText.textContent = progress;
            manualScoreText.textContent = scoreTextContent;
        } else if (currentGameMode === 'seat') {
            seatProgressText.textContent = progress;
            seatScoreText.textContent = scoreTextContent;
        } else if (currentGameMode === 'click-seat') {
            clickSeatProgressText.textContent = progress;
            clickSeatScoreText.textContent = scoreTextContent;
        }
    }

    function shuffleArray(array) {
        for (let i = array.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]];
        }
    }

    // Event Listeners
    startBtn.addEventListener('click', startTraining);
    restartBtn.addEventListener('click', restartTraining);
    
    quitBtn.addEventListener('click', quitGame);
    
    manualQuitBtn.addEventListener('click', quitManualGame);
    submitManualAnswerBtn.addEventListener('click', handleManualAnswer);
    hintGroupBtn.addEventListener('click', handleHintGroup);
    hintInitialBtn.addEventListener('click', handleHintInitial);
    lastnameInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.keyCode === 13) {
            event.preventDefault();
            if (!submitManualAnswerBtn.disabled) {
                submitManualAnswerBtn.click();
            }
        }
    });
    
    seatQuitBtn.addEventListener('click', quitSeatGame);
    submitSeatAnswerBtn.addEventListener('click', handleSeatAnswer);
    seatInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.keyCode === 13) {
            event.preventDefault();
            if (!submitSeatAnswerBtn.disabled) {
                submitSeatAnswerBtn.click();
            }
        }
    });
    
    clickSeatQuitBtn.addEventListener('click', quitClickSeatGame);
    
    searchBtn.addEventListener('click', showSearchScreen);
    searchBackBtn.addEventListener('click', hideSearchScreen);
    searchCognomeInput.addEventListener('input', renderSearchResults);
    searchNomeInput.addEventListener('input', renderSearchResults);
    searchGruppoSelect.addEventListener('change', renderSearchResults);
    searchCommitteeSelect.addEventListener('change', renderSearchResults);
    searchShowCessati.addEventListener('input', renderSearchResults); // NUOVO
    
    modalCloseBtn.addEventListener('click', hideModal);
    modalOverlay.addEventListener('click', (event) => {
        if (event.target === modalOverlay) {
            hideModal();
        }
    });
    
    viewEmicicloBtn.addEventListener('click', showEmicicloMap);
    emicicloViewCloseBtn.addEventListener('click', hideEmicicloMap);


    initialize();
    
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('/service-worker.js')
                .then(registration => {
                    console.log('Service Worker registrato con successo:', registration);
                })
                .catch(error => {
                    console.log('Registrazione del Service Worker fallita:', error);
                });
        });
    }
});