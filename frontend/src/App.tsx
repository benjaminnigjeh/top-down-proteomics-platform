import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Layout from '@/components/Layout'
import Home from '@/pages/Home'
import UploadPage from '@/pages/Upload'
import Jobs from '@/pages/Jobs'
import JobDetail from '@/pages/JobDetail'
import ResultDetail from '@/pages/Results'
import About from '@/pages/About'
import ConvertPage from '@/pages/Convert'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 10_000 },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<Home />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/jobs" element={<Jobs />} />
            <Route path="/jobs/:jobId" element={<JobDetail />} />
            <Route path="/jobs/:jobId/results/:resultId" element={<ResultDetail />} />
            <Route path="/about" element={<About />} />
            <Route path="/convert" element={<ConvertPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
