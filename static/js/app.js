// Espera a que el contenido del DOM esté cargado
document.addEventListener('DOMContentLoaded', () => {

    // Selecciona el interruptor y el tag <html>
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    const htmlElement = document.documentElement;

    // Función para cambiar el tema
    function toggleDarkMode() {
        if (darkModeToggle.checked) {
            htmlElement.classList.add('dark-mode');
            // Opcional: Guardar preferencia en localStorage
            localStorage.setItem('theme', 'dark');
        } else {
            htmlElement.classList.remove('dark-mode');
            // Opcional: Guardar preferencia en localStorage
            localStorage.setItem('theme', 'light');
        }
    }

    // Comprobar la preferencia guardada al cargar la página
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        darkModeToggle.checked = true;
        htmlElement.classList.add('dark-mode');
    } else {
        // Por defecto o si está guardado 'light'
        darkModeToggle.checked = false;
        htmlElement.classList.remove('dark-mode');
    }

    // Añadir el listener al interruptor
    if (darkModeToggle) {
        darkModeToggle.addEventListener('change', toggleDarkMode);
    }

});

document.addEventListener('DOMContentLoaded', () => {

    // Selecciona los elementos del chat (solo si existen en esta página)
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input-field');
    const messagesContainer = document.getElementById('chat-messages-container');
    
    // *** NUEVOS ELEMENTOS DE CARGA ***
    const loadingBar = document.getElementById('loading-bar');

    // Si no estamos en la página del chatbot, no hagas nada
    if (!chatForm || !chatInput || !messagesContainer || !loadingBar) {
        return;
    }

    // Manejador para el envío del formulario
    chatForm.addEventListener('submit', async (event) => {
        event.preventDefault(); // Evita que la página se recargue

        const messageText = chatInput.value.trim();
        if (messageText === '') {
            return; // No envíes mensajes vacíos
        }

        // 1. Muestra el mensaje del usuario en la UI
        addMessage(messageText, 'user');
        
        // 2. Limpia el campo de texto
        chatInput.value = '';

        // 3. *** INICIA LA BARRA DE CARGA ***
        chatForm.classList.add('is-loading'); // Bloquea el input y botón
        loadingBar.style.width = '0%'; // Resetea la barra
        
        // Anima rápidamente al 90% para simular progreso
        setTimeout(() => {
            if (chatForm.classList.contains('is-loading')) { // Solo si sigue cargando
                 loadingBar.style.width = '90%';
            }
        }, 100); // 100ms después de enviar

        try {
            // 4. Envía el mensaje al backend (API)
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: messageText }),
            });

            // 5. *** COMPLETA LA BARRA DE CARGA ***
            loadingBar.style.width = '100%'; // Anima al 100%

            // Espera medio segundo (para que se vea el 100%) y luego oculta
            setTimeout(() => {
                chatForm.classList.remove('is-loading'); // Desbloquea el input
                // Resetea la barra para la próxima vez (después de ocultarse)
                setTimeout(() => { loadingBar.style.width = '0%'; }, 500);
            }, 500); 

            if (!response.ok) {
                // Maneja errores del servidor
                throw new Error('Error en la respuesta del servidor.');
            }

            const data = await response.json();

            if (data.error) {
                // Maneja errores lógicos del backend
                addMessage(data.error, 'bot-error');
            } else {
                // 6. Muestra la respuesta del bot en la UI
                addMessage(data.reply, 'bot', data.model);
            }

        } catch (error) {
            console.error('Error al contactar al chatbot:', error);
            
            // *** OCULTA LA BARRA EN CASO DE ERROR ***
            chatForm.classList.remove('is-loading');
            loadingBar.style.width = '0%';

            addMessage('Lo siento, no pude conectarme con el servidor. Inténtalo de nuevo.', 'bot-error');
        }
    });

    /**
     * Añade un nuevo mensaje a la ventana de chat.
     * (Esta función es la misma que ya tenías)
     */
    function addMessage(text, type, model = null) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', type);
        
        // Reemplaza saltos de línea (\n) con <br> para formato HTML
        text = text.replace(/\n/g, '<br>');
        messageElement.innerHTML = text; // Usamos innerHTML para renderizar los <br>

        // (Opcional) Añade la etiqueta del modelo si se proporciona
        if (model) {
            const modelTag = document.createElement('span');
            modelTag.classList.add('model-tag');
            modelTag.textContent = `vía ${model}`;
            messageElement.appendChild(modelTag);
        }

        messagesContainer.appendChild(messageElement);
        
        // Hace scroll automático al último mensaje
        scrollToBottom();
    }

    /**
     * (Las funciones showTypingIndicator y removeTypingIndicator
     * han sido eliminadas ya que no se usan)
     */

    /** Hace scroll al fondo del contenedor de mensajes */
    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
});