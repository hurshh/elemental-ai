import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Upload, 
  Loader2, 
  Package, 
  Scale, 
  DollarSign, 
  FileText, 
  Sparkles,
  ChevronRight,
  AlertTriangle,
  CheckCircle2,
  Info,
  Globe,
  Truck,
  BarChart3,
  Layers,
  X
} from 'lucide-react'
import axios from 'axios'

// Types
interface Component {
  name: string
  quantity: number
  material: string
  dimensions: string
  weight_per_unit_kg: number
  weight_total_kg: number
  raw_materials: Record<string, number>
  data_source: string
  identification_logic?: string
}

interface TariffData {
  hs_code_classification: {
    primary_hs_code: string
    hs_code_description: string
    classification_reasoning: string
  }
  tariff_rates: {
    base_duty_rate_percent: number
    mfn_rate_source?: string
    effective_total_rate_percent: number
    additional_duties: Array<{
      name: string
      rate_percent: number
      applies: boolean
      reason: string
    }>
  }
  estimated_duties: {
    estimated_product_value_usd: number
    total_estimated_duty_usd: number
    duty_per_kg_usd: number
  }
  material_tariff_breakdown: Array<{
    material: string
    percentage_of_product: number
    material_duty_rate: number
    notes: string
  }>
  ai_insights: {
    cost_optimization_suggestions: string[]
    risk_factors: string[]
    recommendation_summary: string
  }
  compliance_requirements: Array<{
    requirement: string
    description: string
    agency: string
  }>
  disclaimers: string[]
}

interface AnalysisReport {
  report: {
    report_metadata: {
      generated_at: string
      image_analyzed: string
      user_context: string | null
    }
    components: Component[]
    weight_summary: {
      total_weight_kg: number
    }
    material_composition: {
      aggregate_percentages: Record<string, number>
    }
    procurement_summary: {
      total_components: number
      total_items: number
    }
  }
  tariff_estimation: {
    tariff_estimation: TariffData
    request_parameters: {
      origin_country: string
      destination_country: string
    }
  }
}

// Loading Animation Component
const LoadingAnimation = () => (
  <div className="flex flex-col items-center justify-center py-20">
    <div className="relative">
      <motion.div
        className="w-24 h-24 rounded-full border-4 border-aurora-cyan/30"
        animate={{ rotate: 360 }}
        transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
      />
      <motion.div
        className="absolute inset-2 rounded-full border-4 border-transparent border-t-aurora-purple"
        animate={{ rotate: -360 }}
        transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
      />
      <motion.div
        className="absolute inset-4 rounded-full border-4 border-transparent border-b-aurora-pink"
        animate={{ rotate: 360 }}
        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
      />
      <Sparkles className="absolute inset-0 m-auto w-8 h-8 text-aurora-cyan" />
    </div>
    <motion.p 
      className="mt-8 text-white/70 text-lg"
      animate={{ opacity: [0.5, 1, 0.5] }}
      transition={{ duration: 2, repeat: Infinity }}
    >
      Analyzing your product...
    </motion.p>
    <div className="loading-dots flex gap-2 mt-4">
      <span className="w-3 h-3 bg-aurora-cyan rounded-full" />
      <span className="w-3 h-3 bg-aurora-purple rounded-full" />
      <span className="w-3 h-3 bg-aurora-pink rounded-full" />
    </div>
  </div>
)

// Upload Zone Component
const UploadZone = ({ 
  onFileSelect, 
  isDragging, 
  setIsDragging 
}: { 
  onFileSelect: (file: File) => void
  isDragging: boolean
  setIsDragging: (v: boolean) => void
}) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    className={`
      relative p-12 rounded-3xl border-2 border-dashed transition-all duration-300 cursor-pointer
      ${isDragging 
        ? 'border-aurora-cyan bg-aurora-cyan/10 scale-[1.02]' 
        : 'border-white/20 hover:border-aurora-purple/50 bg-white/5'
      }
    `}
    onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
    onDragLeave={() => setIsDragging(false)}
    onDrop={(e) => {
      e.preventDefault()
      setIsDragging(false)
      const file = e.dataTransfer.files[0]
      if (file) onFileSelect(file)
    }}
    onClick={() => document.getElementById('file-input')?.click()}
  >
    <input
      id="file-input"
      type="file"
      accept="image/*"
      className="hidden"
      onChange={(e) => e.target.files?.[0] && onFileSelect(e.target.files[0])}
    />
    <div className="flex flex-col items-center text-center">
      <motion.div
        animate={{ y: isDragging ? -10 : 0 }}
        className="w-20 h-20 rounded-2xl bg-gradient-to-br from-aurora-cyan/20 to-aurora-purple/20 flex items-center justify-center mb-6"
      >
        <Upload className="w-10 h-10 text-aurora-cyan" />
      </motion.div>
      <h3 className="text-xl font-semibold text-white mb-2">
        Drop your product image here
      </h3>
      <p className="text-white/50">
        or click to browse • PNG, JPG, WEBP up to 16MB
      </p>
    </div>
  </motion.div>
)

// Stats Card Component
const StatsCard = ({ 
  icon: Icon, 
  label, 
  value, 
  subvalue,
  color = 'cyan',
  delay = 0
}: { 
  icon: any
  label: string
  value: string
  subvalue?: string
  color?: 'cyan' | 'purple' | 'pink' | 'blue'
  delay?: number
}) => {
  const colors = {
    cyan: 'from-aurora-cyan/20 to-aurora-cyan/5 border-aurora-cyan/30',
    purple: 'from-aurora-purple/20 to-aurora-purple/5 border-aurora-purple/30',
    pink: 'from-aurora-pink/20 to-aurora-pink/5 border-aurora-pink/30',
    blue: 'from-aurora-blue/20 to-aurora-blue/5 border-aurora-blue/30',
  }
  const iconColors = {
    cyan: 'text-aurora-cyan',
    purple: 'text-aurora-purple',
    pink: 'text-aurora-pink',
    blue: 'text-aurora-blue',
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className={`glass rounded-2xl p-5 bg-gradient-to-br ${colors[color]}`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-white/50 text-sm mb-1">{label}</p>
          <p className="text-2xl font-bold text-white">{value}</p>
          {subvalue && <p className="text-white/40 text-sm mt-1">{subvalue}</p>}
        </div>
        <div className={`p-3 rounded-xl bg-white/5 ${iconColors[color]}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </motion.div>
  )
}

// Material Bar Component
const MaterialBar = ({ 
  material, 
  percentage, 
  delay 
}: { 
  material: string
  percentage: number
  delay: number 
}) => (
  <motion.div
    initial={{ opacity: 0, x: -20 }}
    animate={{ opacity: 1, x: 0 }}
    transition={{ delay }}
    className="mb-3"
  >
    <div className="flex justify-between text-sm mb-1">
      <span className="text-white/70 capitalize">{material.replace(/_/g, ' ')}</span>
      <span className="text-white font-medium">{percentage.toFixed(1)}%</span>
    </div>
    <div className="h-2 bg-white/10 rounded-full overflow-hidden">
      <motion.div
        initial={{ width: 0 }}
        animate={{ width: `${percentage}%` }}
        transition={{ delay: delay + 0.2, duration: 0.8, ease: "easeOut" }}
        className="h-full rounded-full bg-gradient-to-r from-aurora-cyan via-aurora-purple to-aurora-pink"
      />
    </div>
  </motion.div>
)

// Component Card
const ComponentCard = ({ 
  component, 
  index 
}: { 
  component: Component
  index: number 
}) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay: index * 0.1 }}
    whileHover={{ scale: 1.02 }}
    className="glass rounded-2xl p-5 hover:bg-white/10 transition-colors"
  >
    <div className="flex items-start justify-between mb-3">
      <div>
        <h4 className="text-white font-semibold">{component.name}</h4>
        <p className="text-white/50 text-sm">{component.material}</p>
      </div>
      <span className="px-3 py-1 rounded-full bg-aurora-cyan/20 text-aurora-cyan text-sm font-medium">
        ×{component.quantity}
      </span>
    </div>
    <div className="grid grid-cols-2 gap-3 text-sm">
      <div>
        <p className="text-white/40">Weight</p>
        <p className="text-white">{component.weight_total_kg?.toFixed(2)} kg</p>
      </div>
      <div>
        <p className="text-white/40">Dimensions</p>
        <p className="text-white text-xs">{component.dimensions}</p>
      </div>
    </div>
    {component.raw_materials && (
      <div className="mt-3 pt-3 border-t border-white/10">
        <p className="text-white/40 text-xs mb-2">Materials</p>
        <div className="flex flex-wrap gap-1">
          {Object.entries(component.raw_materials).map(([mat, pct]) => (
            <span key={mat} className="px-2 py-0.5 rounded-full bg-white/10 text-white/70 text-xs">
              {mat}: {pct}%
            </span>
          ))}
        </div>
      </div>
    )}
  </motion.div>
)

// Tariff Insight Card
const InsightCard = ({ 
  title, 
  items, 
  icon: Icon,
  variant = 'info'
}: { 
  title: string
  items: string[]
  icon: any
  variant?: 'info' | 'warning' | 'success'
}) => {
  const variants = {
    info: 'from-aurora-blue/20 to-aurora-blue/5 border-aurora-blue/30',
    warning: 'from-amber-500/20 to-amber-500/5 border-amber-500/30',
    success: 'from-emerald-500/20 to-emerald-500/5 border-emerald-500/30',
  }
  const iconVariants = {
    info: 'text-aurora-blue',
    warning: 'text-amber-400',
    success: 'text-emerald-400',
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`glass rounded-2xl p-5 bg-gradient-to-br ${variants[variant]}`}
    >
      <div className="flex items-center gap-3 mb-4">
        <Icon className={`w-5 h-5 ${iconVariants[variant]}`} />
        <h4 className="text-white font-semibold">{title}</h4>
      </div>
      <ul className="space-y-2">
        {items.map((item, i) => (
          <motion.li
            key={i}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.1 }}
            className="flex items-start gap-2 text-white/70 text-sm"
          >
            <ChevronRight className="w-4 h-4 mt-0.5 text-white/40 flex-shrink-0" />
            {item}
          </motion.li>
        ))}
      </ul>
    </motion.div>
  )
}

// Main App Component
function App() {
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const [report, setReport] = useState<AnalysisReport | null>(null)
  const [activeTab, setActiveTab] = useState<'overview' | 'components' | 'tariffs' | 'materials'>('overview')
  const [context, setContext] = useState('')
  const [originCountry, setOriginCountry] = useState('China')
  const [destCountry, setDestCountry] = useState('United States')
  const [declaredValue, setDeclaredValue] = useState('')

  const handleFileSelect = (selectedFile: File) => {
    setFile(selectedFile)
    setPreview(URL.createObjectURL(selectedFile))
  }

  const handleAnalyze = async () => {
    if (!file) return

    setIsLoading(true)
    const formData = new FormData()
    formData.append('image', file)
    if (context) formData.append('context', context)
    formData.append('origin_country', originCountry)
    formData.append('destination_country', destCountry)
    if (declaredValue) formData.append('declared_value', declaredValue)

    try {
      const response = await axios.post('http://localhost:5001/api/analyze', formData)
      setReport(response.data.analysis)
    } catch (error) {
      console.error('Analysis failed:', error)
      // Load demo data on error
      const demoResponse = await axios.get('http://localhost:5001/api/demo')
      setReport(demoResponse.data.analysis)
    } finally {
      setIsLoading(false)
    }
  }

  const loadDemo = async () => {
    setIsLoading(true)
    try {
      const response = await axios.get('http://localhost:5001/api/demo')
      setReport(response.data.analysis)
      setPreview('/demo-product.jpg')
    } catch (error) {
      console.error('Failed to load demo:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const resetAnalysis = () => {
    setFile(null)
    setPreview(null)
    setReport(null)
  }

  const tabs = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'components', label: 'Components', icon: Package },
    { id: 'materials', label: 'Materials', icon: Layers },
    { id: 'tariffs', label: 'Trade Impact', icon: DollarSign },
  ]

  return (
    <div className="min-h-screen animated-gradient">
      {/* Aurora background effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-aurora-purple/20 rounded-full blur-[100px] animate-pulse-slow" />
        <div className="absolute top-1/2 -left-40 w-80 h-80 bg-aurora-cyan/20 rounded-full blur-[100px] animate-pulse-slow" style={{ animationDelay: '1s' }} />
        <div className="absolute -bottom-40 right-1/3 w-80 h-80 bg-aurora-pink/20 rounded-full blur-[100px] animate-pulse-slow" style={{ animationDelay: '2s' }} />
      </div>

      <div className="relative max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <motion.header 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-aurora-cyan to-aurora-purple flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-4xl font-bold text-gradient">Elemental AI</h1>
          </div>
          <p className="text-white/60 text-lg max-w-2xl mx-auto">
            AI-powered product analysis, bill of materials extraction, and tariff estimation
          </p>
        </motion.header>

        <AnimatePresence mode="wait">
          {!report && !isLoading && (
            <motion.div
              key="upload"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="max-w-3xl mx-auto"
            >
              <UploadZone 
                onFileSelect={handleFileSelect}
                isDragging={isDragging}
                setIsDragging={setIsDragging}
              />

              {preview && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-8"
                >
                  {/* Preview */}
                  <div className="glass rounded-2xl p-4 mb-6">
                    <div className="flex items-center gap-4">
                      <img 
                        src={preview} 
                        alt="Preview" 
                        className="w-24 h-24 object-cover rounded-xl"
                      />
                      <div className="flex-1">
                        <p className="text-white font-medium">{file?.name}</p>
                        <p className="text-white/50 text-sm">
                          {file && (file.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                      <button
                        onClick={() => { setFile(null); setPreview(null) }}
                        className="p-2 rounded-xl hover:bg-white/10 text-white/50 hover:text-white transition-colors"
                      >
                        <X className="w-5 h-5" />
                      </button>
                    </div>
                  </div>

                  {/* Options */}
                  <div className="glass rounded-2xl p-6 mb-6">
                    <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                      <Info className="w-4 h-4 text-aurora-cyan" />
                      Analysis Options
                    </h3>
                    <div className="grid md:grid-cols-2 gap-4">
                      <div>
                        <label className="text-white/50 text-sm block mb-2">Context (optional)</label>
                        <input
                          type="text"
                          value={context}
                          onChange={(e) => setContext(e.target.value)}
                          placeholder="e.g., wooden furniture, metal frame"
                          className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-white/30 focus:outline-none focus:border-aurora-cyan/50"
                        />
                      </div>
                      <div>
                        <label className="text-white/50 text-sm block mb-2">Declared Value (USD)</label>
                        <input
                          type="number"
                          value={declaredValue}
                          onChange={(e) => setDeclaredValue(e.target.value)}
                          placeholder="e.g., 500"
                          className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-white/30 focus:outline-none focus:border-aurora-cyan/50"
                        />
                      </div>
                      <div>
                        <label className="text-white/50 text-sm block mb-2">Origin Country</label>
                        <select
                          value={originCountry}
                          onChange={(e) => setOriginCountry(e.target.value)}
                          className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-aurora-cyan/50"
                        >
                          <option value="China">China</option>
                          <option value="Vietnam">Vietnam</option>
                          <option value="India">India</option>
                          <option value="Mexico">Mexico</option>
                          <option value="Germany">Germany</option>
                        </select>
                      </div>
                      <div>
                        <label className="text-white/50 text-sm block mb-2">Destination Country</label>
                        <select
                          value={destCountry}
                          onChange={(e) => setDestCountry(e.target.value)}
                          className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-aurora-cyan/50"
                        >
                          <option value="United States">United States</option>
                          <option value="European Union">European Union</option>
                          <option value="United Kingdom">United Kingdom</option>
                          <option value="Canada">Canada</option>
                        </select>
                      </div>
                    </div>
                  </div>

                  {/* Analyze Button */}
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={handleAnalyze}
                    className="w-full py-4 rounded-2xl bg-gradient-to-r from-aurora-cyan via-aurora-purple to-aurora-pink text-white font-semibold text-lg shadow-lg aurora-glow hover:shadow-xl transition-shadow"
                  >
                    <span className="flex items-center justify-center gap-2">
                      <Sparkles className="w-5 h-5" />
                      Analyze Product
                    </span>
                  </motion.button>
                </motion.div>
              )}

              {/* Demo Button */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
                className="text-center mt-8"
              >
                <button
                  onClick={loadDemo}
                  className="text-white/50 hover:text-white transition-colors underline underline-offset-4"
                >
                  or try with demo data
                </button>
              </motion.div>
            </motion.div>
          )}

          {isLoading && (
            <motion.div
              key="loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <LoadingAnimation />
            </motion.div>
          )}

          {report && !isLoading && (
            <motion.div
              key="report"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              {/* Back Button */}
              <motion.button
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                onClick={resetAnalysis}
                className="mb-6 flex items-center gap-2 text-white/50 hover:text-white transition-colors"
              >
                <ChevronRight className="w-4 h-4 rotate-180" />
                Analyze another product
              </motion.button>

              {/* Tabs */}
              <div className="glass rounded-2xl p-2 mb-8 inline-flex gap-1">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    className={`
                      px-5 py-2.5 rounded-xl flex items-center gap-2 transition-all font-medium
                      ${activeTab === tab.id 
                        ? 'bg-gradient-to-r from-aurora-cyan to-aurora-purple text-white' 
                        : 'text-white/50 hover:text-white hover:bg-white/5'
                      }
                    `}
                  >
                    <tab.icon className="w-4 h-4" />
                    {tab.label}
                  </button>
                ))}
              </div>

              {/* Tab Content */}
              <AnimatePresence mode="wait">
                {activeTab === 'overview' && (
                  <motion.div
                    key="overview"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                  >
                    {/* Stats Grid */}
                    <div className="grid md:grid-cols-4 gap-4 mb-8">
                      <StatsCard
                        icon={Package}
                        label="Total Components"
                        value={report.report.procurement_summary.total_components.toString()}
                        subvalue={`${report.report.procurement_summary.total_items} items total`}
                        color="cyan"
                        delay={0}
                      />
                      <StatsCard
                        icon={Scale}
                        label="Total Weight"
                        value={`${report.report.weight_summary.total_weight_kg.toFixed(1)} kg`}
                        color="purple"
                        delay={0.1}
                      />
                      <StatsCard
                        icon={DollarSign}
                        label="Estimated Duty"
                        value={`$${report.tariff_estimation.tariff_estimation.estimated_duties.total_estimated_duty_usd.toFixed(2)}`}
                        subvalue={`${report.tariff_estimation.tariff_estimation.tariff_rates.effective_total_rate_percent}% rate`}
                        color="pink"
                        delay={0.2}
                      />
                      <StatsCard
                        icon={Globe}
                        label="Trade Route"
                        value={report.tariff_estimation.request_parameters.origin_country}
                        subvalue={`→ ${report.tariff_estimation.request_parameters.destination_country}`}
                        color="blue"
                        delay={0.3}
                      />
                    </div>

                    <div className="grid lg:grid-cols-2 gap-8">
                      {/* Material Composition */}
                      <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.4 }}
                        className="glass rounded-2xl p-6"
                      >
                        <h3 className="text-white font-semibold mb-6 flex items-center gap-2">
                          <Layers className="w-5 h-5 text-aurora-purple" />
                          Material Composition
                        </h3>
                        {Object.entries(report.report.material_composition.aggregate_percentages)
                          .sort(([,a], [,b]) => b - a)
                          .map(([material, percentage], i) => (
                            <MaterialBar
                              key={material}
                              material={material}
                              percentage={percentage}
                              delay={0.5 + i * 0.05}
                            />
                          ))
                        }
                      </motion.div>

                      {/* AI Insights */}
                      <div className="space-y-4">
                        <InsightCard
                          title="Cost Optimization"
                          items={report.tariff_estimation.tariff_estimation.ai_insights.cost_optimization_suggestions.slice(0, 3)}
                          icon={Sparkles}
                          variant="success"
                        />
                        <InsightCard
                          title="Risk Factors"
                          items={report.tariff_estimation.tariff_estimation.ai_insights.risk_factors}
                          icon={AlertTriangle}
                          variant="warning"
                        />
                      </div>
                    </div>

                    {/* Recommendation */}
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.6 }}
                      className="mt-8 glass rounded-2xl p-6 bg-gradient-to-r from-aurora-cyan/10 to-aurora-purple/10 border-aurora-cyan/20"
                    >
                      <div className="flex items-start gap-4">
                        <div className="p-3 rounded-xl bg-aurora-cyan/20">
                          <CheckCircle2 className="w-6 h-6 text-aurora-cyan" />
                        </div>
                        <div>
                          <h4 className="text-white font-semibold mb-2">AI Recommendation</h4>
                          <p className="text-white/70">
                            {report.tariff_estimation.tariff_estimation.ai_insights.recommendation_summary}
                          </p>
                        </div>
                      </div>
                    </motion.div>
                  </motion.div>
                )}

                {activeTab === 'components' && (
                  <motion.div
                    key="components"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    className="grid md:grid-cols-2 lg:grid-cols-3 gap-4"
                  >
                    {report.report.components.map((component, i) => (
                      <ComponentCard key={i} component={component} index={i} />
                    ))}
                  </motion.div>
                )}

                {activeTab === 'materials' && (
                  <motion.div
                    key="materials"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                  >
                    <div className="glass rounded-2xl overflow-hidden">
                      <table className="w-full">
                        <thead className="bg-white/5">
                          <tr>
                            <th className="text-left text-white/50 font-medium px-6 py-4">Material</th>
                            <th className="text-left text-white/50 font-medium px-6 py-4">Percentage</th>
                            <th className="text-left text-white/50 font-medium px-6 py-4">HS Chapter</th>
                            <th className="text-left text-white/50 font-medium px-6 py-4">Duty Rate</th>
                            <th className="text-left text-white/50 font-medium px-6 py-4">Notes</th>
                          </tr>
                        </thead>
                        <tbody>
                          {report.tariff_estimation.tariff_estimation.material_tariff_breakdown.map((mat, i) => (
                            <motion.tr
                              key={mat.material}
                              initial={{ opacity: 0, x: -20 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ delay: i * 0.05 }}
                              className="border-t border-white/5"
                            >
                              <td className="px-6 py-4 text-white capitalize">{mat.material.replace(/_/g, ' ')}</td>
                              <td className="px-6 py-4 text-white">{mat.percentage_of_product.toFixed(1)}%</td>
                              <td className="px-6 py-4">
                                <span className="px-2 py-1 rounded-lg bg-aurora-purple/20 text-aurora-purple text-sm">
                                  Ch. 44
                                </span>
                              </td>
                              <td className="px-6 py-4 text-white">{mat.material_duty_rate}%</td>
                              <td className="px-6 py-4 text-white/50 text-sm">{mat.notes}</td>
                            </motion.tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </motion.div>
                )}

                {activeTab === 'tariffs' && (
                  <motion.div
                    key="tariffs"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    className="space-y-6"
                  >
                    {/* HS Code Classification */}
                    <div className="glass rounded-2xl p-6">
                      <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                        <FileText className="w-5 h-5 text-aurora-cyan" />
                        HS Code Classification
                      </h3>
                      <div className="grid md:grid-cols-2 gap-6">
                        <div>
                          <p className="text-white/50 text-sm mb-1">Primary HS Code</p>
                          <p className="text-2xl font-bold text-gradient">
                            {report.tariff_estimation.tariff_estimation.hs_code_classification.primary_hs_code}
                          </p>
                        </div>
                        <div>
                          <p className="text-white/50 text-sm mb-1">Description</p>
                          <p className="text-white">
                            {report.tariff_estimation.tariff_estimation.hs_code_classification.hs_code_description}
                          </p>
                        </div>
                      </div>
                      <div className="mt-4 pt-4 border-t border-white/10">
                        <p className="text-white/50 text-sm mb-1">Classification Reasoning</p>
                        <p className="text-white/70">
                          {report.tariff_estimation.tariff_estimation.hs_code_classification.classification_reasoning}
                        </p>
                      </div>
                    </div>

                    {/* Duty Breakdown */}
                    <div className="grid md:grid-cols-2 gap-6">
                      <div className="glass rounded-2xl p-6">
                        <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                          <DollarSign className="w-5 h-5 text-aurora-pink" />
                          Duty Calculation
                        </h3>
                        <div className="space-y-3">
                          <div className="flex justify-between">
                            <span className="text-white/50">Product Value</span>
                            <span className="text-white font-medium">
                              ${report.tariff_estimation.tariff_estimation.estimated_duties.estimated_product_value_usd.toFixed(2)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-white/50">Effective Rate</span>
                            <span className="text-aurora-cyan font-semibold">
                              {report.tariff_estimation.tariff_estimation.tariff_rates.effective_total_rate_percent}%
                            </span>
                          </div>
                          {report.tariff_estimation.tariff_estimation.tariff_rates.additional_duties
                            .filter(d => d.applies)
                            .map((duty, i) => (
                              <div key={i} className="flex justify-between">
                                <span className="text-amber-400">{duty.name}</span>
                                <span className="text-amber-400">+{duty.rate_percent}%</span>
                              </div>
                            ))
                          }
                          <div className="pt-3 border-t border-white/10 flex justify-between">
                            <span className="text-white font-semibold">Total Duty</span>
                            <span className="text-2xl font-bold text-gradient">
                              ${report.tariff_estimation.tariff_estimation.estimated_duties.total_estimated_duty_usd.toFixed(2)}
                            </span>
                          </div>
                        </div>
                      </div>

                      <div className="glass rounded-2xl p-6">
                        <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                          <Truck className="w-5 h-5 text-aurora-purple" />
                          Compliance Requirements
                        </h3>
                        <div className="space-y-3">
                          {report.tariff_estimation.tariff_estimation.compliance_requirements.map((req, i) => (
                            <div key={i} className="p-3 rounded-xl bg-white/5">
                              <p className="text-white font-medium text-sm">{req.requirement}</p>
                              <p className="text-white/50 text-xs mt-1">{req.agency}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Disclaimers */}
                    <div className="glass rounded-2xl p-6 bg-amber-500/5 border-amber-500/20">
                      <h4 className="text-amber-400 font-semibold mb-3 flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4" />
                        Important Disclaimers
                      </h4>
                      <ul className="space-y-2">
                        {report.tariff_estimation.tariff_estimation.disclaimers.map((disclaimer, i) => (
                          <li key={i} className="text-white/60 text-sm flex items-start gap-2">
                            <span className="text-amber-400">•</span>
                            {disclaimer}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}

export default App
