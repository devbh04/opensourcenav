"use client"

import { PageHeader } from "@/components/repository/page-header"
import { FilterForm } from "@/components/repository/filter-form"
import { RepositoryTable } from "@/components/repository/repository-table"
import { ErrorDisplay } from "@/components/repository/error-display"

export default function RepositoryRecommendation() {
  return (
    <div className="w-full space-y-6 bg-black text-gray-100 p-6 min-h-screen">
      <PageHeader />
      <FilterForm />
      <ErrorDisplay />
      <RepositoryTable />
    </div>
  )
}
