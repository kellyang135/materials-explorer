/**
 * Exploration Tracking Service
 * Captures user discovery patterns for guided discovery mode
 */

export interface ExplorationEvent {
  type: 'material_view' | 'search' | 'filter' | 'property_focus' | 'comparison';
  timestamp: number;
  data: {
    materialId?: string;
    materialFormula?: string;
    crystalSystem?: string;
    searchQuery?: string;
    filterType?: string;
    filterValue?: string;
    property?: string;
    comparedMaterials?: string[];
    sessionId: string;
  };
}

export interface ExplorationSession {
  sessionId: string;
  startTime: number;
  events: ExplorationEvent[];
  currentContext: {
    focusAreas: string[];  // e.g., ['solid_electrolytes', 'high_conductivity']
    materialTypes: string[];  // e.g., ['Li-compounds', 'garnets']
    exploredProperties: string[];  // e.g., ['ionic_conductivity', 'stability']
  };
}

class ExplorationTracker {
  private session: ExplorationSession;
  private readonly STORAGE_KEY = 'materials_exploration_session';

  constructor() {
    this.session = this.initializeSession();
  }

  private initializeSession(): ExplorationSession {
    // Try to restore session from localStorage
    const stored = localStorage.getItem(this.STORAGE_KEY);
    if (stored) {
      try {
        const parsed = JSON.parse(stored) as ExplorationSession;
        // Only restore if session is less than 2 hours old
        if (Date.now() - parsed.startTime < 2 * 60 * 60 * 1000) {
          return parsed;
        }
      } catch (e) {
        console.warn('Could not restore exploration session');
      }
    }

    // Create new session
    return {
      sessionId: this.generateSessionId(),
      startTime: Date.now(),
      events: [],
      currentContext: {
        focusAreas: [],
        materialTypes: [],
        exploredProperties: []
      }
    };
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substring(7)}`;
  }

  private saveSession(): void {
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.session));
  }

  private updateContext(event: ExplorationEvent): void {
    const { currentContext } = this.session;
    const { data } = event;

    // Update focus areas based on behavior patterns
    if (event.type === 'material_view' && data.crystalSystem) {
      if (!currentContext.materialTypes.includes(data.crystalSystem)) {
        currentContext.materialTypes.push(data.crystalSystem);
      }
    }

    // Detect focus areas from search patterns
    if (event.type === 'search' && data.searchQuery) {
      const query = data.searchQuery.toLowerCase();
      const focusKeywords = {
        'electrolyte': 'solid_electrolytes',
        'cathode': 'cathode_materials',
        'conductivity': 'high_conductivity',
        'stable': 'stability_focus',
        'cost': 'cost_conscious',
        'energy': 'energy_density'
      };

      Object.entries(focusKeywords).forEach(([keyword, focus]) => {
        if (query.includes(keyword) && !currentContext.focusAreas.includes(focus)) {
          currentContext.focusAreas.push(focus);
        }
      });
    }

    // Track property interests
    if (event.type === 'property_focus' && data.property) {
      if (!currentContext.exploredProperties.includes(data.property)) {
        currentContext.exploredProperties.push(data.property);
      }
    }
  }

  // Public methods for tracking events
  trackMaterialView(materialId: string, materialFormula: string, crystalSystem?: string): void {
    const event: ExplorationEvent = {
      type: 'material_view',
      timestamp: Date.now(),
      data: {
        materialId,
        materialFormula,
        crystalSystem,
        sessionId: this.session.sessionId
      }
    };

    this.session.events.push(event);
    this.updateContext(event);
    this.saveSession();

    console.log('🔍 Tracked material view:', materialFormula);
  }

  trackSearch(query: string): void {
    const event: ExplorationEvent = {
      type: 'search',
      timestamp: Date.now(),
      data: {
        searchQuery: query,
        sessionId: this.session.sessionId
      }
    };

    this.session.events.push(event);
    this.updateContext(event);
    this.saveSession();

    console.log('🔎 Tracked search:', query);
  }

  trackFilter(filterType: string, filterValue: string): void {
    const event: ExplorationEvent = {
      type: 'filter',
      timestamp: Date.now(),
      data: {
        filterType,
        filterValue,
        sessionId: this.session.sessionId
      }
    };

    this.session.events.push(event);
    this.updateContext(event);
    this.saveSession();

    console.log('🎛️ Tracked filter:', filterType, '=', filterValue);
  }

  trackPropertyFocus(property: string): void {
    const event: ExplorationEvent = {
      type: 'property_focus',
      timestamp: Date.now(),
      data: {
        property,
        sessionId: this.session.sessionId
      }
    };

    this.session.events.push(event);
    this.updateContext(event);
    this.saveSession();

    console.log('📊 Tracked property focus:', property);
  }

  trackComparison(materialIds: string[]): void {
    const event: ExplorationEvent = {
      type: 'comparison',
      timestamp: Date.now(),
      data: {
        comparedMaterials: materialIds,
        sessionId: this.session.sessionId
      }
    };

    this.session.events.push(event);
    this.updateContext(event);
    this.saveSession();

    console.log('⚖️ Tracked comparison:', materialIds);
  }

  // Analysis methods for guided discovery
  getExplorationPath(): ExplorationEvent[] {
    return this.session.events.slice(); // Return copy
  }

  getRecentMaterials(count: number = 5): string[] {
    return this.session.events
      .filter(e => e.type === 'material_view' && e.data.materialFormula)
      .slice(-count)
      .map(e => e.data.materialFormula!)
      .reverse();
  }

  getCurrentFocusAreas(): string[] {
    return this.session.currentContext.focusAreas.slice();
  }

  getMaterialTypes(): string[] {
    return this.session.currentContext.materialTypes.slice();
  }

  getExploredProperties(): string[] {
    return this.session.currentContext.exploredProperties.slice();
  }

  // Detect exploration patterns
  detectExplorationPattern(): string {
    const events = this.session.events;
    const recentEvents = events.slice(-10); // Last 10 events

    // Pattern: Comparing similar materials
    const materialViews = recentEvents.filter(e => e.type === 'material_view');
    if (materialViews.length >= 3) {
      const crystalSystems = materialViews
        .map(e => e.data.crystalSystem)
        .filter(cs => cs);
      
      if (new Set(crystalSystems).size === 1 && crystalSystems.length >= 3) {
        return `exploring_${crystalSystems[0]}_materials`;
      }
    }

    // Pattern: Property-focused exploration
    const propertyFocuses = recentEvents.filter(e => e.type === 'property_focus');
    if (propertyFocuses.length >= 2) {
      return 'property_focused_exploration';
    }

    // Pattern: Search-driven discovery
    const searches = recentEvents.filter(e => e.type === 'search');
    if (searches.length >= 2) {
      return 'search_driven_exploration';
    }

    return 'general_exploration';
  }

  // Reset session (for testing or new exploration)
  resetSession(): void {
    localStorage.removeItem(this.STORAGE_KEY);
    this.session = this.initializeSession();
    console.log('🔄 Reset exploration session');
  }

  // Get session summary for debugging
  getSessionSummary(): object {
    return {
      sessionId: this.session.sessionId,
      duration: Date.now() - this.session.startTime,
      eventCount: this.session.events.length,
      currentContext: this.session.currentContext,
      explorationPattern: this.detectExplorationPattern(),
      recentMaterials: this.getRecentMaterials()
    };
  }
}

// Export singleton instance
export const explorationTracker = new ExplorationTracker();

// Export type for components that need to use the tracker
export default ExplorationTracker;