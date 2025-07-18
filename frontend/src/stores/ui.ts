// frontend/src/stores/ui.ts
import { defineStore } from 'pinia';
import { v4 as uuidv4 } from 'uuid';

export interface Notification {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  message: string;
  duration?: number;
}

// NEW: Interface for confirmation dialog state
export interface ConfirmationDialog {
  id: string;
  title: string;
  message: string;
  resolve: (value: boolean) => void; // Function to resolve the Promise with user's choice
  reject: (reason?: any) => void;   // Function to reject the Promise if dialog is dismissed
  confirmText?: string;             // Text for the confirm button (default: 'Confirm')
  cancelText?: string;              // Text for the cancel button (default: 'Cancel')
}


export const useUiStore = defineStore('ui', {
  state: () => ({
    notifications: [] as Notification[],
    globalLoading: false,
    // NEW: State for the active confirmation dialog
    activeConfirmation: null as ConfirmationDialog | null,
  }),
  actions: {
    // --- Notification Actions (Existing) ---
    addNotification(type: Notification['type'], message: string, duration: number = 5000) {
      const id = uuidv4();
      const newNotification: Notification = { id, type, message, duration };
      this.notifications.push(newNotification);

      if (duration > 0) {
        setTimeout(() => {
          this.removeNotification(id);
        }, duration);
      }
    },
    removeNotification(id: string) {
      this.notifications = this.notifications.filter(n => n.id !== id);
    },
    showSuccessToast(message: string, duration?: number) { this.addNotification('success', message, duration); },
    showErrorToast(message: string, duration?: number) { this.addNotification('error', message, duration); },
    showInfoToast(message: string, duration?: number) { this.addNotification('info', message, duration); },
    showWarningToast(message: string, duration?: number) { this.addNotification('warning', message, duration); },

    setGlobalLoading(isLoading: boolean) { this.globalLoading = isLoading; },

    // --- NEW: Confirmation Dialog Actions ---
    /**
     * Shows a confirmation dialog and returns a Promise that resolves with true/false.
     * @param title Title of the dialog.
     * @param message Message content of the dialog.
     * @param confirmText Optional text for the confirm button.
     * @param cancelText Optional text for the cancel button.
     * @returns Promise<boolean> True if confirmed, false if cancelled/dismissed.
     */
    showConfirmation(
      title: string,
      message: string,
      confirmText: string = 'Confirm',
      cancelText: string = 'Cancel'
    ): Promise<boolean> {
      return new Promise((resolve, reject) => {
        this.activeConfirmation = {
          id: uuidv4(), // Unique ID for keying if multiple are ever stacked (though usually one at a time)
          title,
          message,
          resolve, // Store the promise's resolve function
          reject,  // Store the promise's reject function
          confirmText,
          cancelText
        };
      });
    },

    /**
     * Closes the confirmation dialog and resolves its promise.
     * @param confirmed True if the user confirmed, false if cancelled.
     */
    _resolveConfirmation(confirmed: boolean) {
      if (this.activeConfirmation) {
        this.activeConfirmation.resolve(confirmed);
        this.activeConfirmation = null; // Clear the dialog state
      }
    },

    /**
     * Closes the confirmation dialog and rejects its promise (e.g., if dismissed externally).
     */
    _rejectConfirmation(reason?: any) {
      if (this.activeConfirmation) {
        this.activeConfirmation.reject(reason);
        this.activeConfirmation = null;
      }
    }
  },
  getters: {
    // No specific getters needed for confirmation dialog yet
  },
});