// --- static/js/app.js ---

document.addEventListener('DOMContentLoaded', () => {
    
    // --- 1. ELEMENTOS DEL DOM ---
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input-field');
    const messagesContainer = document.getElementById('chat-messages-container');
    const loadingFace = document.getElementById('loading-face');
    const btnRegenerate = document.getElementById('btn-regenerate');

    // Validación básica
    if (!chatForm || !messagesContainer) return;

    // --- 2. FUNCIONES DE INTERFAZ ---

    // Agrega un mensaje visualmente al chat
    function addMessage(text, sender) {
        const div = document.createElement('div');
        div.classList.add('message', sender);
        
        if (sender === 'bot') {
            div.innerHTML = text; 
        } else {
            div.textContent = text;
        }

        messagesContainer.appendChild(div);
        
        // Scroll al fondo
        messagesContainer.scrollTo({
            top: messagesContainer.scrollHeight,
            behavior: 'smooth'
        });
    }

    // [MODIFICADO] Función de borrado más agresiva
    function removeLastBotMessage() {
        // Obtenemos el último elemento físico dentro del contenedor de mensajes
        const lastElement = messagesContainer.lastElementChild;

        // Verificamos: ¿Existe? ¿Tiene la clase 'bot'?
        if (lastElement && lastElement.classList.contains('bot')) {
            // Lo eliminamos directamente del DOM
            lastElement.remove();
            console.log("✅ Último mensaje del bot eliminado correctamente.");
        } else {
            // Si el último no es del bot (raro), buscamos en la lista completa
            const botMessages = messagesContainer.querySelectorAll('.message.bot');
            if (botMessages.length > 0) {
                botMessages[botMessages.length - 1].remove();
                console.log("✅ Último mensaje del bot eliminado (método alternativo).");
            }
        }
    }

    // --- 3. LÓGICA DE COMUNICACIÓN ---

    async function sendMessage(message, mode = 'normal') {
        
        // Si es regeneración, ocultamos botón y mostramos carga
        if (mode === 'regenerate') {
            if(btnRegenerate) btnRegenerate.style.display = 'none';
            if(loadingFace) loadingFace.style.display = 'block';
        } 
        // Si es normal
        else {
            addMessage(message, 'user');
            chatInput.value = '';
            if(loadingFace) loadingFace.style.display = 'block';
            if(btnRegenerate) btnRegenerate.style.display = 'none';
        }
        
        // Asegurar scroll
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message, mode: mode })
            });
            
            const data = await response.json();
            
            if(loadingFace) loadingFace.style.display = 'none';

            if (data.error) {
                const divError = document.createElement('div');
                divError.classList.add('message', 'bot');
                divError.style.color = 'red';
                divError.textContent = "Error: " + data.error;
                messagesContainer.appendChild(divError);
            } else {
                // Agregar la NUEVA respuesta
                addMessage(data.reply, 'bot');
                
                // Mostrar botón regenerar
                if(btnRegenerate) btnRegenerate.style.display = 'inline-block';
            }

        } catch (error) {
            if(loadingFace) loadingFace.style.display = 'none';
            console.error("Error:", error);
            addMessage("Error de conexión.", 'bot');
        }
    }

    // --- 4. EVENTOS ---

    // Enviar mensaje
    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const message = chatInput.value.trim();
        if (message) {
            sendMessage(message, 'normal');
        }
    });

    // Clic en Regenerar
    if (btnRegenerate) {
        btnRegenerate.addEventListener('click', () => {
            console.log("🔄 Botón regenerar presionado.");
            
            // 1. PRIMERO: Borramos la respuesta anterior
            removeLastBotMessage();

            // 2. LUEGO: Pedimos la nueva
            sendMessage("", 'regenerate');
        });
    }
});