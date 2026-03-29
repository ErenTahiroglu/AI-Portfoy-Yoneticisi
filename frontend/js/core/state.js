// Simple Reactive State Manager using Proxy
(function() {
    window.createStore = function(initialState) {
        const listeners = [];
        
        const state = new Proxy(initialState, {
            set(target, property, value) {
                if (target[property] === value) return true;
                const oldValue = target[property];
                target[property] = value;
                
                // Notify listeners
                listeners.forEach(fn => fn(property, value, oldValue, target));
                return true;
            }
        });

        // Add subscribe method to the state object itself
        Object.defineProperty(state, 'subscribe', {
            value: function(fn) {
                listeners.push(fn);
                // Run initially for all current keys
                Object.keys(initialState).forEach(key => fn(key, initialState[key], undefined, initialState));
                return () => {
                    const idx = listeners.indexOf(fn);
                    if (idx > -1) listeners.splice(idx, 1);
                };
            },
            enumerable: false,
            writable: false
        });

        return state;
    };
})();
