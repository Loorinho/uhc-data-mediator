
import { createServerFn } from '@tanstack/react-start'
import { z } from 'zod'
import api from './api.server'
import type { TypedApiResponse } from '@/types/types'

export const canonicalTransformationSchema  =  z.object({
        acquisitionId: z.string().min(1,"Acquisition ID is required"),
        productCode: z.string().min(1,"Product code is required"),
      })

export type CanonicalTransformationResponse = {
  releaseId: string,
  acquisitionId: string,
  productCode: string,
  version: string,
  status: string,
  transformationStatus: string,
  qualityStatus: string,
}

export const triggerCanonicalTransformation =
  createServerFn({ method: 'POST' })
    .validator(
      canonicalTransformationSchema
    )
    .handler(async ({ data }) => {
      const dataToSend = {
        productCode: data.productCode,
      }
      const response = await api.post<TypedApiResponse<CanonicalTransformationResponse>>(
        `/interoperability/acquisition/${data.acquisitionId}/transform/`,
        dataToSend,
        {
				validateStatus: () => true,
			});


      return response.data
    })
