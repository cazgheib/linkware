import React, { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { loadStripe } from '@stripe/stripe-js'
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js'
import { 
  Crown, 
  Check, 
  Shield, 
  Users, 
  BookOpen, 
  Headphones,
  TrendingUp,
  Building
} from 'lucide-react'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY || 'pk_test_placeholder')

const membershipPlans = [
  {
    id: 'free',
    name: 'Free',
    price: 0,
    period: 'forever',
    icon: <BookOpen className="h-8 w-8 text-gray-600" />,
    description: 'Perfect for getting started with basic content',
    features: [
      'Access to free blog posts',
      'Basic market insights',
      'Community forum access',
      'Email newsletter'
    ],
    limitations: [
      'Limited premium content',
      'No direct expert access',
      'Basic support only'
    ]
  },
  {
    id: 'premium',
    name: 'Premium',
    price: 49,
    period: 'month',
    icon: <Crown className="h-8 w-8 text-yellow-500" />,
    description: 'Ideal for professionals seeking advanced insights',
    features: [
      'All free features',
      'Access to premium blog posts',
      'Advanced trading strategies',
      'Monthly expert webinars',
      'Priority community support',
      'Downloadable resources',
      'Market analysis reports'
    ],
    popular: true
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    price: 199,
    period: 'month',
    icon: <Building className="h-8 w-8 text-purple-600" />,
    description: 'Complete solution for teams and organizations',
    features: [
      'All premium features',
      'Team collaboration tools',
      'Custom integrations',
      'Dedicated account manager',
      '24/7 priority support',
      'Custom training sessions',
      'API access',
      'White-label options'
    ]
  }
]

interface CheckoutFormProps {
  planId: string
  planName: string
  price: number
  onSuccess: () => void
  onCancel: () => void
}

const CheckoutForm: React.FC<CheckoutFormProps> = ({ planId, price, onSuccess, onCancel }) => {
  const stripe = useStripe()
  const elements = useElements()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    
    if (!stripe || !elements) {
      return
    }

    setLoading(true)
    setError('')

    const cardElement = elements.getElement(CardElement)
    
    if (!cardElement) {
      setError('Card element not found')
      setLoading(false)
      return
    }

    try {
      const { error: stripeError, paymentMethod } = await stripe.createPaymentMethod({
        type: 'card',
        card: cardElement,
      })

      if (stripeError) {
        setError(stripeError.message || 'Payment failed')
        setLoading(false)
        return
      }

      const response = await axios.post(`${API_BASE_URL}/api/membership/create-payment-intent`, {
        membership_type: planId,
        payment_method_id: paymentMethod.id
      })

      const { client_secret } = response.data

      const { error: confirmError } = await stripe.confirmCardPayment(client_secret)

      if (confirmError) {
        setError(confirmError.message || 'Payment confirmation failed')
      } else {
        await axios.post(`${API_BASE_URL}/api/membership/upgrade`, {
          membership_type: planId
        })
        onSuccess()
      }
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Payment failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="p-4 border rounded-lg">
        <CardElement
          options={{
            style: {
              base: {
                fontSize: '16px',
                color: '#424770',
                '::placeholder': {
                  color: '#aab7c4',
                },
              },
            },
          }}
        />
      </div>
      
      {error && (
        <div className="text-red-600 text-sm">{error}</div>
      )}
      
      <div className="flex space-x-4">
        <Button type="button" variant="outline" onClick={onCancel} className="flex-1">
          Cancel
        </Button>
        <Button type="submit" disabled={!stripe || loading} className="flex-1">
          {loading ? 'Processing...' : `Pay $${price}/month`}
        </Button>
      </div>
    </form>
  )
}

export const MembershipPage: React.FC = () => {
  const { user, refreshUser } = useAuth()
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null)
  const [showCheckout, setShowCheckout] = useState(false)

  const currentPlan = membershipPlans.find(plan => plan.id === user?.membership_type) || membershipPlans[0]

  const handleUpgrade = (planId: string) => {
    if (planId === 'free') {
      return
    }
    setSelectedPlan(planId)
    setShowCheckout(true)
  }

  const handlePaymentSuccess = async () => {
    setShowCheckout(false)
    setSelectedPlan(null)
    await refreshUser()
  }

  const handlePaymentCancel = () => {
    setShowCheckout(false)
    setSelectedPlan(null)
  }

  const selectedPlanData = membershipPlans.find(plan => plan.id === selectedPlan)

  if (showCheckout && selectedPlanData) {
    return (
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Complete Your Upgrade</h1>
          <p className="text-gray-600">
            Upgrading to {selectedPlanData.name} - ${selectedPlanData.price}/month
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              {selectedPlanData.icon}
              <span>{selectedPlanData.name} Membership</span>
            </CardTitle>
            <CardDescription>
              Enter your payment information to complete the upgrade
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Elements stripe={stripePromise}>
              <CheckoutForm
                planId={selectedPlanData.id}
                planName={selectedPlanData.name}
                price={selectedPlanData.price}
                onSuccess={handlePaymentSuccess}
                onCancel={handlePaymentCancel}
              />
            </Elements>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">Choose Your Membership</h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Unlock premium content and advanced features designed for capital markets professionals
        </p>
      </div>

      <div className="mb-8 text-center">
        <div className="inline-flex items-center space-x-2 bg-blue-50 px-4 py-2 rounded-full">
          <span className="text-sm text-blue-800">Current Plan:</span>
          <Badge variant={currentPlan.id === 'free' ? 'secondary' : currentPlan.id === 'premium' ? 'default' : 'destructive'}>
            {currentPlan.name}
          </Badge>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
        {membershipPlans.map((plan) => (
          <Card 
            key={plan.id} 
            className={`relative ${plan.popular ? 'ring-2 ring-blue-500 shadow-lg' : ''} ${
              plan.id === user?.membership_type ? 'bg-blue-50 border-blue-200' : ''
            }`}
          >
            {plan.popular && (
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                <Badge className="bg-blue-500 text-white">Most Popular</Badge>
              </div>
            )}
            
            <CardHeader className="text-center">
              <div className="flex justify-center mb-4">
                {plan.icon}
              </div>
              <CardTitle className="text-2xl">{plan.name}</CardTitle>
              <CardDescription className="text-sm">{plan.description}</CardDescription>
              <div className="mt-4">
                <span className="text-4xl font-bold text-gray-900">
                  ${plan.price}
                </span>
                <span className="text-gray-600">/{plan.period}</span>
              </div>
            </CardHeader>
            
            <CardContent>
              <div className="space-y-3 mb-6">
                {plan.features.map((feature, index) => (
                  <div key={index} className="flex items-start space-x-3">
                    <Check className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                    <span className="text-sm text-gray-700">{feature}</span>
                  </div>
                ))}
                {plan.limitations?.map((limitation, index) => (
                  <div key={index} className="flex items-start space-x-3 opacity-60">
                    <span className="h-5 w-5 flex-shrink-0 mt-0.5 text-gray-400">×</span>
                    <span className="text-sm text-gray-500">{limitation}</span>
                  </div>
                ))}
              </div>
              
              {plan.id === user?.membership_type ? (
                <Button className="w-full" disabled>
                  Current Plan
                </Button>
              ) : plan.id === 'free' ? (
                <Button variant="outline" className="w-full" disabled>
                  Downgrade Not Available
                </Button>
              ) : (
                <Button 
                  className="w-full" 
                  onClick={() => handleUpgrade(plan.id)}
                  variant={plan.popular ? 'default' : 'outline'}
                >
                  Upgrade to {plan.name}
                </Button>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="bg-gray-50 rounded-lg p-8">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Why Upgrade?</h2>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Join thousands of professionals who rely on our platform for cutting-edge insights 
            and tools in capital markets technology.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="text-center">
            <TrendingUp className="h-12 w-12 text-blue-600 mx-auto mb-4" />
            <h3 className="font-semibold text-gray-900 mb-2">Advanced Analytics</h3>
            <p className="text-sm text-gray-600">
              Deep market insights and trading strategies
            </p>
          </div>
          
          <div className="text-center">
            <Users className="h-12 w-12 text-green-600 mx-auto mb-4" />
            <h3 className="font-semibold text-gray-900 mb-2">Expert Community</h3>
            <p className="text-sm text-gray-600">
              Connect with industry professionals
            </p>
          </div>
          
          <div className="text-center">
            <Shield className="h-12 w-12 text-purple-600 mx-auto mb-4" />
            <h3 className="font-semibold text-gray-900 mb-2">Risk Management</h3>
            <p className="text-sm text-gray-600">
              Comprehensive risk assessment tools
            </p>
          </div>
          
          <div className="text-center">
            <Headphones className="h-12 w-12 text-orange-600 mx-auto mb-4" />
            <h3 className="font-semibold text-gray-900 mb-2">Priority Support</h3>
            <p className="text-sm text-gray-600">
              24/7 dedicated customer support
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
