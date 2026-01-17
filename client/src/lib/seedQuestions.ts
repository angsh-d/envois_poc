/**
 * Seed questions for the Clinical AI Chat Assistant by screen/context
 *
 * Design principles:
 * - Each question is crisp and under 15 words
 * - Questions are module-specific
 * - Agentic questions (isAgentic: true) demonstrate multi-source synthesis
 */

export interface SeedQuestion {
  text: string
  isAgentic: boolean
}

export interface ContextQuestions {
  questions: SeedQuestion[]
  description: string
}

export const SEED_QUESTIONS: Record<string, ContextQuestions> = {
  // Landing Page - Portfolio Overview
  landing: {
    description: 'Portfolio-level insights across all studies',
    questions: [
      {
        text: 'Which studies are at highest risk of missing regulatory milestones?',
        isAgentic: true
      },
      {
        text: 'Summarize enrollment health across all active studies',
        isAgentic: true
      },
      {
        text: 'What requires my attention today?',
        isAgentic: true
      }
    ]
  },

  // Study Selection
  'study-select': {
    description: 'Cross-study comparison and selection',
    questions: [
      {
        text: 'Compare safety profiles across my hip revision studies',
        isAgentic: true
      },
      {
        text: 'Which study has the most protocol deviations?',
        isAgentic: false
      },
      {
        text: 'Show studies approaching their enrollment deadline',
        isAgentic: false
      }
    ]
  },

  // Executive Dashboard
  dashboard: {
    description: 'Study overview and executive insights',
    questions: [
      {
        text: 'How do our revision and dislocation rates compare to registry and literature benchmarks?',
        isAgentic: true
      },
      {
        text: 'Generate python code for a Kaplan-Meier survival analysis for revision-free survival in our study',
        isAgentic: true
      },
      {
        text: 'Generate an executive summary of study progress for leadership',
        isAgentic: true
      }
    ]
  },

  // Readiness Assessment
  readiness: {
    description: 'Regulatory submission readiness',
    questions: [
      {
        text: 'What is driving our safety signals and how do our observed rates compare to the literature and registry defined thresholds?',
        isAgentic: true
      },
      {
        text: 'What gaps exist between our data and MDR PMCF requirements?',
        isAgentic: true
      },
      {
        text: 'Prioritize actions to improve our submission readiness score',
        isAgentic: true
      }
    ]
  },

  // Safety Signals
  safety: {
    description: 'Adverse event monitoring and safety analysis',
    questions: [
      {
        text: 'What are the complication rates by study site - which sites are underperforming?',
        isAgentic: true
      },
      {
        text: 'Cross-reference our AE patterns with MAUDE database reports',
        isAgentic: true
      },
      {
        text: 'Which adverse events are trending above expected rates?',
        isAgentic: false
      }
    ]
  },

  // Protocol Deviations
  deviations: {
    description: 'Protocol compliance and deviation tracking',
    questions: [
      {
        text: 'Identify sites with systemic deviation patterns',
        isAgentic: true
      },
      {
        text: "What's the root cause of our top 3 deviation categories?",
        isAgentic: true
      },
      {
        text: 'How do our deviation rates compare to FDA audit thresholds?',
        isAgentic: true
      }
    ]
  },

  // Risk Stratification
  risk: {
    description: 'Patient risk analysis and outcome prediction',
    questions: [
      {
        text: 'Which patient cohorts are driving outcome uncertainty?',
        isAgentic: true
      },
      {
        text: 'What literature supports our hazard ratio assumptions?',
        isAgentic: true
      },
      {
        text: 'How would excluding age >80 impact our success probability?',
        isAgentic: false
      }
    ]
  },

  // Protocol Management
  protocol: {
    description: 'Protocol design and regulatory alignment',
    questions: [
      {
        text: 'Compare our inclusion criteria to competitor studies',
        isAgentic: true
      },
      {
        text: 'Flag protocol sections that may conflict with EU MDR',
        isAgentic: true
      },
      {
        text: 'What endpoint changes would strengthen our regulatory position?',
        isAgentic: true
      }
    ]
  },

  // Data Sources
  'data-sources': {
    description: 'Data integration and quality assessment',
    questions: [
      {
        text: 'Which data sources have quality issues affecting analysis?',
        isAgentic: true
      },
      {
        text: 'Map our data fields to FDA eCTD submission requirements',
        isAgentic: true
      },
      {
        text: 'Are there gaps between registry data and our CRF data?',
        isAgentic: true
      }
    ]
  },

  // Multi-Agent Architecture
  agents: {
    description: 'AI agent transparency and explainability',
    questions: [
      {
        text: 'Show me the reasoning chain for the last extraction',
        isAgentic: false
      },
      {
        text: 'Which agents contributed to the safety signal detection?',
        isAgentic: false
      },
      {
        text: 'Why did the model disagree with manual clinical review?',
        isAgentic: true
      }
    ]
  },

  // Simulation Studio (Monte Carlo)
  simulation: {
    description: 'Outcome modeling and scenario analysis',
    questions: [
      {
        text: 'What enrollment changes would increase our pass probability to 85%?',
        isAgentic: true
      },
      {
        text: 'Validate these hazard ratios against latest ortho literature',
        isAgentic: true
      },
      {
        text: 'Which risk factors contribute most to outcome variance?',
        isAgentic: false
      }
    ]
  },

  // Competitive Intelligence (PM-focused)
  competitive: {
    description: 'Competitive landscape and sales enablement',
    questions: [
      {
        text: 'Generate a battle card vs Zimmer Biomet revision cups',
        isAgentic: true
      },
      {
        text: 'What are our key differentiators based on registry data?',
        isAgentic: true
      },
      {
        text: 'How does our 2-year survival rate compare to competitors?',
        isAgentic: false
      },
      {
        text: "What's our competitive position in the revision hip market?",
        isAgentic: true
      }
    ]
  },

  // Claim Validation (PM and Marketing focused)
  claims: {
    description: 'Marketing claim substantiation',
    questions: [
      {
        text: 'Can we claim "95% survival at 2 years" in marketing materials?',
        isAgentic: true
      },
      {
        text: 'What claims can we substantiate with our current clinical data?',
        isAgentic: true
      },
      {
        text: 'Is the claim "superior outcomes vs competitors" compliant?',
        isAgentic: true
      },
      {
        text: 'What evidence gaps exist for our key marketing claims?',
        isAgentic: false
      }
    ]
  }
}

/**
 * Get seed questions for a specific context
 * Falls back to dashboard questions if context not found
 */
export function getSeedQuestions(context: string): SeedQuestion[] {
  const contextQuestions = SEED_QUESTIONS[context]
  if (contextQuestions) {
    return contextQuestions.questions
  }
  // Fallback to dashboard
  return SEED_QUESTIONS.dashboard.questions
}

/**
 * Get formatted question strings for display
 */
export function getSeedQuestionStrings(context: string): string[] {
  return getSeedQuestions(context).map(q => q.text)
}
