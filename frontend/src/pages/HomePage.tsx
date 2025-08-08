import React from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { 
  TrendingUp, 
  Shield, 
  Cloud, 
  Users, 
  BookOpen, 
  Crown,
  ArrowRight,
  CheckCircle
} from 'lucide-react'

export const HomePage: React.FC = () => {
  const { user } = useAuth()

  const features = [
    {
      icon: <TrendingUp className="h-8 w-8 text-blue-600" />,
      title: "Algorithmic Trading",
      description: "Advanced trading systems and market analysis tools for capital markets professionals."
    },
    {
      icon: <Shield className="h-8 w-8 text-green-600" />,
      title: "Risk Management",
      description: "Comprehensive risk assessment and compliance frameworks for financial institutions."
    },
    {
      icon: <Cloud className="h-8 w-8 text-purple-600" />,
      title: "Cloud Infrastructure",
      description: "Scalable cloud solutions designed specifically for financial services and trading platforms."
    },
    {
      icon: <Users className="h-8 w-8 text-orange-600" />,
      title: "Expert Community",
      description: "Connect with industry professionals and share insights on capital markets technology."
    }
  ]

  const membershipBenefits = [
    "Access to premium educational content",
    "Industry insights and market analysis",
    "Exclusive webinars and events",
    "Direct access to expert consultations",
    "Advanced trading tools and resources",
    "Priority support and community access"
  ]

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-blue-50 to-indigo-100 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
              <span className="text-blue-600">Linkware</span>
              <span className="text-2xl md:text-3xl text-gray-600 ml-2">Consulting</span>
              <span className="block text-xl md:text-2xl mt-4 text-gray-700">IT Solutions for Capital Markets</span>
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
              Empowering financial professionals with cutting-edge technology solutions, 
              educational resources, and industry insights for modern capital markets.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button size="lg" asChild>
                <Link to="/blog" className="flex items-center space-x-2">
                  <BookOpen size={20} />
                  <span>Explore Content</span>
                  <ArrowRight size={16} />
                </Link>
              </Button>
              {!user && (
                <>
                  <Button size="lg" asChild>
                    <Link to="/register" className="flex items-center space-x-2">
                      <span>Get Started Free</span>
                      <ArrowRight size={16} />
                    </Link>
                  </Button>
                  <Button variant="outline" size="lg" asChild>
                    <Link to="/login">Sign In</Link>
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Comprehensive IT Solutions
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              From algorithmic trading to risk management, we provide the technology 
              infrastructure that powers modern capital markets.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <Card key={index} className="text-center hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex justify-center mb-4">
                    {feature.icon}
                  </div>
                  <CardTitle className="text-xl">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-gray-600">
                    {feature.description}
                  </CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Membership Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Join Our Professional Community
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Get access to premium content, expert insights, and exclusive resources 
              designed for capital markets professionals.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h3 className="text-2xl font-bold text-gray-900 mb-6">
                Premium Membership Benefits
              </h3>
              <div className="space-y-4">
                {membershipBenefits.map((benefit, index) => (
                  <div key={index} className="flex items-start space-x-3">
                    <CheckCircle className="h-6 w-6 text-green-500 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-700">{benefit}</span>
                  </div>
                ))}
              </div>
              <div className="mt-8">
                {user ? (
                  <Button size="lg" asChild>
                    <Link to="/membership" className="flex items-center space-x-2">
                      <Crown size={20} />
                      <span>Upgrade Membership</span>
                    </Link>
                  </Button>
                ) : (
                  <Button size="lg" asChild>
                    <Link to="/register" className="flex items-center space-x-2">
                      <span>Start Free Trial</span>
                      <ArrowRight size={16} />
                    </Link>
                  </Button>
                )}
              </div>
            </div>

            <div className="bg-white p-8 rounded-lg shadow-lg">
              <div className="text-center">
                <Crown className="h-16 w-16 text-yellow-500 mx-auto mb-4" />
                <h4 className="text-2xl font-bold text-gray-900 mb-2">Premium Access</h4>
                <p className="text-gray-600 mb-6">
                  Unlock exclusive content and advanced features with our premium membership.
                </p>
                <div className="text-4xl font-bold text-blue-600 mb-2">$49</div>
                <div className="text-gray-500 mb-6">per month</div>
                <Button className="w-full" size="lg" asChild>
                  <Link to={user ? "/membership" : "/register"}>
                    {user ? "Upgrade Now" : "Get Started"}
                  </Link>
                </Button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-blue-600">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Ready to Transform Your Capital Markets Technology?
          </h2>
          <p className="text-xl text-blue-100 mb-8 max-w-2xl mx-auto">
            Join thousands of professionals who trust our platform for their 
            capital markets technology needs.
          </p>
          <Button size="lg" variant="secondary" asChild>
            <Link to="/blog" className="flex items-center space-x-2">
              <span>Explore Content</span>
              <ArrowRight size={16} />
            </Link>
          </Button>
        </div>
      </section>
    </div>
  )
}
