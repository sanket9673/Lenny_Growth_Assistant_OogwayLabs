import React, { useState } from 'react'

export function App() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return
    setLoading(true)
    setHasSearched(true)
    try {
      const res = await fetch(`/api/v1/search?query=${encodeURIComponent(query)}&limit=3`)
      const data = await res.json()
      setResults(data.results || [])
    } catch (err) {
      console.error("Search error:", err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 text-slate-100 p-6 sm:p-12 flex flex-col items-center">
      <header className="max-w-3xl w-full text-center my-12">
        <div className="inline-block bg-indigo-500/10 text-indigo-400 text-xs font-semibold tracking-widest uppercase px-3 py-1 rounded-full border border-indigo-500/20 mb-4">
          Expert Growth RAG Engine
        </div>
        <h1 className="text-4xl sm:text-5xl font-black tracking-tight bg-gradient-to-r from-indigo-400 via-purple-400 to-indigo-200 bg-clip-text text-transparent mb-4">
          Lenny Growth Assistant
        </h1>
        <p className="text-slate-400 text-lg max-w-2xl mx-auto">
          Query product strategies, growth frameworks, and career advice directly from transcripts of Lenny's Podcast.
        </p>
      </header>

      <main className="max-w-3xl w-full">
        <form onSubmit={handleSearch} className="flex gap-3 mb-10">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask anything (e.g., How to achieve product market fit?)"
            className="flex-1 bg-slate-900/60 backdrop-blur-sm border border-slate-800 rounded-xl px-5 py-4 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
          />
          <button
            type="submit"
            disabled={loading}
            className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold px-8 py-4 rounded-xl transition-all shadow-lg shadow-indigo-600/20 active:scale-95 disabled:opacity-50 disabled:active:scale-100"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </form>

        <section className="space-y-6">
          {loading && (
            <div className="flex flex-col items-center justify-center py-12">
              <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-indigo-500 mb-4"></div>
              <p className="text-slate-400 text-sm">Embedding query and searching index...</p>
            </div>
          )}

          {!loading && results.map((res, i) => (
            <div
              key={i}
              className="bg-slate-900/40 backdrop-blur-md border border-slate-800/80 rounded-2xl p-6 shadow-xl hover:border-slate-700/60 transition-all duration-300"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4 pb-3 border-b border-slate-800/50">
                <div>
                  <span className="text-indigo-400 font-bold block sm:inline">{res.guest_name}</span>
                  <span className="text-slate-500 hidden sm:inline"> — </span>
                  <span className="text-slate-300 italic text-sm">{res.transcript_title}</span>
                </div>
                <div className="flex items-center gap-2 self-start sm:self-auto">
                  {res.speaker && (
                    <span className="text-xs bg-slate-800 text-slate-400 px-2.5 py-1 rounded-md">
                      Speaker: {res.speaker}
                    </span>
                  )}
                  {res.timestamp_start && (
                    <span className="text-xs bg-slate-800 text-slate-400 px-2.5 py-1 rounded-md">
                      {res.timestamp_start}
                    </span>
                  )}
                  <span className="text-xs font-mono bg-indigo-950/60 text-indigo-300 border border-indigo-800/50 px-2.5 py-1 rounded-md">
                    Similarity: {res.similarity}
                  </span>
                </div>
              </div>
              <p className="text-slate-300 text-base leading-relaxed whitespace-pre-wrap">
                {res.content}
              </p>
            </div>
          ))}

          {!loading && hasSearched && results.length === 0 && (
            <div className="bg-slate-900/20 border border-dashed border-slate-800 rounded-2xl py-16 text-center">
              <p className="text-slate-500 text-lg">No matching insights found.</p>
              <p className="text-slate-600 text-sm mt-1">Try expanding your search query.</p>
            </div>
          )}
        </section>
      </main>
    </div>
  )
}

export default App
