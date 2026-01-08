/**
 * Background service worker for Vox Navigator Firefox extension.
 * 
 * This script handles:
 * - Context menu registration ("Ler texto")
 * - Text selection capture from active tab
 * - TTS server communication (POST to http://127.0.0.1:8000/tts)
 * - Audio playback in the browser
 * 
 * Architecture:
 * - No UI pages, popups, or options
 * - Local-only (127.0.0.1)
 * - Synchronous flow: select text → synthesize → play
 */

// TTS server configuration
const TTS_SERVER_URL = 'http://127.0.0.1:8000/tts';

// Context menu ID
const CONTEXT_MENU_ID = 'vox-navigator-read-text';

/**
 * Initialize the extension on install/startup.
 * Registers the context menu item.
 */
function initializeExtension() {
  // Create context menu item
  browser.contextMenus.create({
    id: CONTEXT_MENU_ID,
    title: 'Ler texto',
    contexts: ['selection'] // Only show when text is selected
  });
  
  console.log('Vox Navigator: Context menu registered');
}

/**
 * Handle context menu click.
 * 
 * When user clicks "Ler texto":
 * 1. Get selected text from active tab
 * 2. Send to TTS server
 * 3. Play audio response
 */
async function handleContextMenuClick(info, tab) {
  if (info.menuItemId !== CONTEXT_MENU_ID) {
    return;
  }
  
  // Get selected text
  const selectedText = info.selectionText;
  
  if (!selectedText || !selectedText.trim()) {
    console.warn('Vox Navigator: No text selected');
    return;
  }
  
  console.log('Vox Navigator: Synthesizing text:', selectedText.substring(0, 50) + '...');
  
  try {
    // Step 1: Send POST request to TTS server
    const response = await fetch(TTS_SERVER_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        text: selectedText
      })
    });
    
    // Step 2: Check if request was successful
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`TTS server error (${response.status}): ${errorText}`);
    }
    
    // Step 3: Get audio data as blob
    const audioBlob = await response.blob();
    
    // Step 4: Create object URL for the audio blob
    const audioUrl = URL.createObjectURL(audioBlob);
    
    // Step 5: Inject script into active tab to play audio
    // We use scripting API to inject code that plays the audio
    // Note: We pass the audioUrl as an argument to the injected function
    await browser.scripting.executeScript({
      target: { tabId: tab.id },
      func: (url) => {
        // Create audio element
        const audio = new Audio(url);
        
        // Play audio automatically
        audio.play().catch(error => {
          console.error('Vox Navigator: Audio playback failed:', error);
        });
        
        // Clean up object URL after playback completes
        audio.addEventListener('ended', () => {
          URL.revokeObjectURL(url);
        });
        
        // Also clean up on error
        audio.addEventListener('error', () => {
          URL.revokeObjectURL(url);
        });
      },
      args: [audioUrl]
    });
    
    console.log('Vox Navigator: Audio playback started');
    
  } catch (error) {
    // Error handling: log to console, don't crash extension
    console.error('Vox Navigator: TTS synthesis failed:', error);
    
    // Optionally show a notification to user (if notification permission is added)
    // For now, just log the error
  }
}

// Event listeners

// Initialize on extension startup
browser.runtime.onStartup.addListener(initializeExtension);
browser.runtime.onInstalled.addListener(initializeExtension);

// Handle context menu clicks
browser.contextMenus.onClicked.addListener(handleContextMenuClick);

// Log extension load
console.log('Vox Navigator: Background service worker loaded');
