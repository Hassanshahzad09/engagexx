import { ArrowRight, CheckCircle, TrendingUp, Target, DollarSign, Facebook, Instagram, Youtube, Twitter, Star, Zap, Shield } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { ImageWithFallback } from './figma/ImageWithFallback';

export default function LandingPage({ onNavigate }) {
  console.log("hi")
  const howItWorks = [
    {
      icon: Target,
      title: 'Post Tasks',
      description: 'Create engagement tasks for your social media platforms with your desired budget and requirements.',
    },
    {
      icon: TrendingUp,
      title: 'Perform Tasks',
      description: 'Browse available tasks, complete them quickly, and submit proof of completion for verification.',
    },
    {
      icon: DollarSign,
      title: 'Earn Rewards',
      description: 'Get paid instantly for completed tasks. Withdraw your earnings anytime to your preferred method.',
    },
  ];

  const testimonials = [
    {
      name: 'Sarah Johnson',
      role: 'Digital Marketer',
      image: 'https://images.unsplash.com/photo-1509924023100-a470ace3c89e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxoYXBweSUyMHByb2Zlc3Npb25hbCUyMHBvcnRyYWl0fGVufDF8fHx8MTc2Mjg4NTM4MHww&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral',
      content: 'Engage X helped me boost my Instagram engagement by 300% in just 2 weeks. Highly recommended!',
      rating: 5,
    },
    {
      name: 'Michael Chen',
      role: 'Content Creator',
      image: 'https://images.unsplash.com/photo-1758691737538-220c1902b1ca?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxidXNpbmVzcyUyMHN1Y2Nlc3MlMjBjZWxlYnJhdGlvbnxlbnwxfHx8fDE3NjI4MDgyNjZ8MA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral',
      content: "I've earned over $2,000 completing tasks in my spare time. The platform is easy to use and payments are fast.",
      rating: 5,
    },
    {
      name: 'Emily Rodriguez',
      role: 'Small Business Owner',
      image: 'https://images.unsplash.com/photo-1752650735943-d0fbf1edce21?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx0ZWFtJTIwY29sbGFib3JhdGlvbiUyMHdvcmtzcGFjZXxlbnwxfHx8fDE3NjI4NjEzNTR8MA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral',
      content: 'Perfect for growing our startup. The quality of engagement is genuine and results speak for themselves.',
      rating: 5,
    },
  ];

  const pricingPlans = [
    {
      name: 'Starter',
      price: '$29',
      period: '/month',
      features: [
        'Up to 50 tasks/month',
        'All social platforms',
        'Basic analytics',
        'Email support',
        '5% platform fee',
      ],
      popular: false,
    },
    {
      name: 'Professional',
      price: '$79',
      period: '/month',
      features: [
        'Up to 200 tasks/month',
        'All social platforms',
        'Advanced analytics',
        'Priority support',
        '3% platform fee',
        'Custom task types',
      ],
      popular: true,
    },
    {
      name: 'Enterprise',
      price: '$199',
      period: '/month',
      features: [
        'Unlimited tasks',
        'All social platforms',
        'Real-time analytics',
        '24/7 dedicated support',
        '1% platform fee',
        'Custom integrations',
        'API access',
      ],
      popular: false,
    },
  ];

  const socialPlatforms = [
    { icon: Facebook, name: 'Facebook', color: '#1877F2' },
    { icon: Instagram, name: 'Instagram', color: '#E4405F' },
    { icon: Youtube, name: 'YouTube', color: '#FF0000' },
    { icon: Twitter, name: 'Twitter', color: '#1DA1F2' },
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="border-b border-gray-100 sticky top-0 bg-white/95 backdrop-blur-sm z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-green-600 rounded-xl flex items-center justify-center">
                <Zap className="w-6 h-6 text-white" />
              </div>
              <span className="text-gray-900">Engage X</span>
            </div>
            <div className="hidden md:flex items-center gap-8">
              <a href="#how-it-works" className="text-gray-600 hover:text-green-600 transition-colors">
                How it Works
              </a>
              <a href="#pricing" className="text-gray-600 hover:text-green-600 transition-colors">
                Pricing
              </a>
              <a href="#testimonials" className="text-gray-600 hover:text-green-600 transition-colors">
                Testimonials
              </a>
            </div>
            <div className="flex items-center gap-3">
              <Button variant="ghost" onClick={() => onNavigate('login')}>
                Login
              </Button>
              <Button
                className="bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white rounded-full"
                onClick={() => onNavigate('login')}
              >
                Get Started
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-green-50 via-white to-green-50/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-32">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="inline-flex items-center gap-2 bg-green-100 text-green-700 px-4 py-2 rounded-full mb-6">
                <Shield className="w-4 h-4" />
                <span className="text-sm">Trusted by 50,000+ users worldwide</span>
              </div>
              <h1 className="text-gray-900 mb-6">
                Grow. Engage. Earn.
              </h1>
              <p className="text-gray-600 mb-8 text-lg">
                The ultimate dual-portal platform connecting brands with engaged audiences. 
                Boost your social media presence or earn money completing simple tasks.
              </p>
              <div className="flex flex-wrap gap-4">
                <Button
                  size="lg"
                  className="bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white rounded-full"
                  onClick={() => onNavigate('login')}
                >
                  Start as Buyer
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
                <Button
                  size="lg"
                  variant="outline"
                  className="rounded-full border-green-200 text-green-700 hover:bg-green-50"
                  onClick={() => onNavigate('login')}
                >
                  Start as Seller
                </Button>
              </div>
              <div className="mt-12 flex flex-wrap gap-8">
                {socialPlatforms.map((platform) => (
                  <div key={platform.name} className="flex items-center gap-2 text-gray-600">
                    <platform.icon className="w-5 h-5" style={{ color: platform.color }} />
                    <span className="text-sm">{platform.name}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-green-400 to-green-600 rounded-3xl blur-3xl opacity-20"></div>
              <ImageWithFallback
                src="https://images.unsplash.com/photo-1752650735943-d0fbf1edce21?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx0ZWFtJTIwY29sbGFib3JhdGlvbiUyMHdvcmtzcGFjZXxlbnwxfHx8fDE3NjI4NjEzNTR8MA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral"
                alt="Engage X Platform"
                className="relative rounded-3xl shadow-2xl w-full"
              />
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-gray-900 mb-4">How It Works</h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Get started in three simple steps. Whether you're looking to grow your brand or earn extra income.
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {howItWorks.map((step, index) => (
              <Card key={index} className="border-gray-100 hover:border-green-200 hover:shadow-lg transition-all duration-300 rounded-2xl">
                <CardHeader>
                  <div className="w-16 h-16 bg-gradient-to-br from-green-500 to-green-600 rounded-2xl flex items-center justify-center mb-4">
                    <step.icon className="w-8 h-8 text-white" />
                  </div>
                  <div className="text-sm text-green-600 mb-2">Step {index + 1}</div>
                  <CardTitle className="text-gray-900">{step.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600">{step.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section id="testimonials" className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-gray-900 mb-4">What Our Users Say</h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Join thousands of satisfied users who have transformed their social media strategy.
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <Card key={index} className="border-gray-100 rounded-2xl hover:shadow-lg transition-shadow">
                <CardContent className="pt-6">
                  <div className="flex gap-1 mb-4">
                    {[...Array(testimonial.rating)].map((_, i) => (
                      <Star key={i} className="w-5 h-5 fill-yellow-400 text-yellow-400" />
                    ))}
                  </div>
                  <p className="text-gray-700 mb-6">"{testimonial.content}"</p>
                  <div className="flex items-center gap-3">
                    <ImageWithFallback
                      src={testimonial.image}
                      alt={testimonial.name}
                      className="w-12 h-12 rounded-full object-cover"
                    />
                    <div>
                      <div className="text-gray-900">{testimonial.name}</div>
                      <div className="text-sm text-gray-500">{testimonial.role}</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-gray-900 mb-4">Simple, Transparent Pricing</h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Choose the plan that fits your needs. No hidden fees, cancel anytime.
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {pricingPlans.map((plan, index) => (
              <Card
                key={index}
                className={`rounded-2xl relative overflow-hidden transition-all duration-300 ${
                  plan.popular
                    ? 'border-green-500 shadow-xl scale-105'
                    : 'border-gray-100 hover:border-green-200 hover:shadow-lg'
                }`}
              >
                {plan.popular && (
                  <div className="absolute top-0 right-0 bg-gradient-to-r from-green-500 to-green-600 text-white px-4 py-1 text-sm rounded-bl-lg">
                    Popular
                  </div>
                )}
                <CardHeader>
                  <CardTitle className="text-gray-900">{plan.name}</CardTitle>
                  <div className="mt-4">
                    <span className="text-gray-900">{plan.price}</span>
                    <span className="text-gray-500">{plan.period}</span>
                  </div>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-3 mb-6">
                    {plan.features.map((feature, i) => (
                      <li key={i} className="flex items-start gap-3">
                        <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                        <span className="text-gray-600">{feature}</span>
                      </li>
                    ))}
                  </ul>
                  <Button
                    className={`w-full rounded-full ${
                      plan.popular
                        ? 'bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white'
                        : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                    }`}
                    onClick={() => onNavigate('login')}
                  >
                    Get Started
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-br from-green-500 to-green-600">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-white mb-6">Ready to Get Started?</h2>
          <p className="text-green-100 mb-8 max-w-2xl mx-auto text-lg">
            Join Engage X today and start growing your social media presence or earning money in minutes.
          </p>
          <Button
            size="lg"
            className="bg-white text-green-600 hover:bg-gray-100 rounded-full"
            onClick={() => onNavigate('login')}
          >
            Create Free Account
            <ArrowRight className="w-5 h-5 ml-2" />
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 bg-gradient-to-br from-green-500 to-green-600 rounded-lg flex items-center justify-center">
                  <Zap className="w-5 h-5 text-white" />
                </div>
                <span className="text-white">Engage X</span>
              </div>
              <p className="text-sm">
                The ultimate platform for social media engagement and earnings.
              </p>
            </div>
            <div>
              <h3 className="text-white mb-4">Product</h3>
              <ul className="space-y-2 text-sm">
                <li><a href="#" className="hover:text-green-500 transition-colors">Features</a></li>
                <li><a href="#" className="hover:text-green-500 transition-colors">Pricing</a></li>
                <li><a href="#" className="hover:text-green-500 transition-colors">API</a></li>
              </ul>
            </div>
            <div>
              <h3 className="text-white mb-4">Company</h3>
              <ul className="space-y-2 text-sm">
                <li><a href="#" className="hover:text-green-500 transition-colors">About</a></li>
                <li><a href="#" className="hover:text-green-500 transition-colors">Blog</a></li>
                <li><a href="#" className="hover:text-green-500 transition-colors">Careers</a></li>
              </ul>
            </div>
            <div>
              <h3 className="text-white mb-4">Support</h3>
              <ul className="space-y-2 text-sm">
                <li><a href="#" className="hover:text-green-500 transition-colors">Help Center</a></li>
                <li><a href="#" className="hover:text-green-500 transition-colors">Contact</a></li>
                <li><a href="#" className="hover:text-green-500 transition-colors">Terms</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 pt-8 text-center text-sm">
            <p>&copy; 2025 Engage X. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
